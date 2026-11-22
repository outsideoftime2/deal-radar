"""Free, conservative collector. Publishes retailer-announced promotions and optionally
reads explicitly configured, permitted product pages with dated JSON-LD offers.
Does not claim exhaustive coverage or bypass retailer access controls.
"""
import datetime as dt
import hashlib
import html
from html.parser import HTMLParser
import json
from pathlib import Path
import urllib.parse
import urllib.request

ROOT = Path(__file__).resolve().parent
NOW = dt.datetime.now(dt.timezone.utc)
TODAY = NOW.date()
STORES = ('target', 'kohls', 'walmart')
HOSTS = {'target':'target.com', 'kohls':'kohls.com', 'walmart':'walmart.com'}
OFFICIAL = {
 'target': ('https://corporate.target.com/press/release/2026/11/target-announces-black-friday-deals-and-giveaways-to-help-families-save-big-on-gifts-they-ll-love-to', '2026-11-17'),
 'kohls': ('https://s204.q4cdn.com/271435555/files/doc_news/Now-Arriving-at-The-North-Kohls-November-Holiday-Savings-Events-2026.pdf', '2026-10-30'),
 'walmart': ('https://corporate.walmart.com/askwalmart/when-are-walmarts-2026-black-friday-and-cyber-monday-deals', None)
}

class Scripts(HTMLParser):
 def __init__(self):
  super().__init__(); self.capture=False; self.buffer=''; self.scripts=[]
 def handle_starttag(self,tag,attrs):
  if tag=='script' and dict(attrs).get('type','').lower()=='application/ld+json':
   self.capture=True; self.buffer=''
 def handle_data(self,data):
  if self.capture:self.buffer+=data
 def handle_endtag(self,tag):
  if tag=='script' and self.capture:
   self.scripts.append(self.buffer); self.capture=False

def allowed(url,store):
 try:
  p=urllib.parse.urlparse(url)
  return p.scheme=='https' and (p.hostname==HOSTS[store] or p.hostname.endswith('.'+HOSTS[store]))
 except (ValueError,TypeError,AttributeError):return False

def walk(obj):
 if isinstance(obj,dict):
  yield obj
  for v in obj.values():yield from walk(v)
 elif isinstance(obj,list):
  for v in obj:yield from walk(v)

def date(s):
 try:return dt.date.fromisoformat(str(s)[:10])
 except (ValueError,TypeError):return None

def stable_id(store,url,title,start):
 return store+'-'+hashlib.sha256((url+'|'+title+'|'+start).encode()).hexdigest()[:16]

def dated_products(url,store):
 request=urllib.request.Request(url,headers={'User-Agent':'FamilyDealRadar/1.1 (public information)','Accept':'text/html'})
 with urllib.request.urlopen(request,timeout=12) as r:
  content=r.read(2_000_000).decode('utf-8','replace')
 parser=Scripts();parser.feed(content)
 for raw in parser.scripts:
  try:obj=json.loads(raw)
  except (ValueError,TypeError):continue
  for item in walk(obj):
   kind=item.get('@type',[]);kind=[kind] if isinstance(kind,str) else kind
   if not isinstance(kind,list) or 'Product' not in kind:continue
   offers=item.get('offers',[]);offers=offers if isinstance(offers,list) else [offers]
   for offer in offers:
    if not isinstance(offer,dict):continue
    start=date(offer.get('validFrom'));end=date(offer.get('priceValidUntil'))
    if not start or not end or end<TODAY or end<start or offer.get('price') is None:continue
    title=str(item.get('name') or '').strip()
    if not title:continue
    yield {'id':stable_id(store,url,title,start.isoformat()),'retailer':store,'title':title,
     'description':str(item.get('description') or '')[:300], 'category':str(item.get('category') or 'Other')[:80],
     'sale_price':str(offer['price']),'regular_price':None,'start_date':start.isoformat(),
     'end_date':end.isoformat(),'url':url,'cities':['all'],
     'availability':'Confirm local pricing and stock at retailer', 'verified':True,
     'verified_at':NOW.isoformat(), 'source_type':'dated_product_metadata'}

def load_json(name,default):
 path=ROOT/name
 return json.loads(path.read_text(encoding='utf-8')) if path.exists() else default

def main():
 deals=[];coverage={}
 # These records are based on dated retailer announcements. They are NOT re-verified live.
 for row in load_json('official_promotions.json',[]):
  store=row.get('retailer');start=date(row.get('start_date'));end=date(row.get('end_date'))
  if store not in STORES or not start or not end or end<TODAY or end<start:continue
  url,published=OFFICIAL[store];title=row['title']
  deals.append({**row,'id':stable_id(store,url,title,start.isoformat()),'url':url,
   'sale_price':None,'regular_price':None,'cities':['all'],
   'description':row.get('description') or 'Retailer-announced promotion; see official source for eligible items and terms.',
   'availability':'National announcement; check your local store', 'verified':True,
   'verified_at':published,'source_type':'retailer_announcement'})
 sources=load_json('sources.json',{});manual=load_json('manual_deals.json',[])
 for store in STORES:
  urls=sources.get(store,[]);issues=[];count=0
  for url in urls:
   if not isinstance(url,str) or not allowed(url,store):issues.append('invalid or off-domain URL');continue
   try:
    found=list(dated_products(url,store));deals.extend(found);count+=len(found)
    if not found:issues.append('no dated product metadata found')
   except Exception as e:issues.append(type(e).__name__)
  announced=sum(d['retailer']==store and d['source_type']=='retailer_announcement' for d in deals)
  coverage[store]={'status':f'{announced} announced promotions; {count} dated product offers; not exhaustive',
   'pages_checked':len(urls),'issues':issues[:10]}
 for d in manual:
  store=d.get('retailer');url=d.get('url','')
  if store not in STORES or not allowed(url,store) or d.get('verified') is not True:continue
  start=date(d.get('start_date'));end=date(d.get('end_date'))
  try:verified=dt.datetime.fromisoformat(d['verified_at'].replace('Z','+00:00'))
  except (KeyError,ValueError,TypeError,AttributeError):continue
  if not start or not end or end<TODAY or verified.tzinfo is None or not dt.timedelta(0)<=NOW-verified<=dt.timedelta(days=3):continue
  if not d.get('title') or not isinstance(d.get('cities'),list):continue
  d=dict(d);d['id']=stable_id(store,url,d['title'],start.isoformat());d['source_type']='manual_verified'
  deals.append(d)
 unique={(d['retailer'],d['url'],d['title'],d['start_date'],d['end_date']):d for d in deals}
 result={'updated_at':NOW.isoformat(timespec='seconds'),'coverage':coverage,'deals':sorted(unique.values(),key=lambda d:(d['start_date'],d['retailer'],d['title']))}
 (ROOT/'deals.json').write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
 print('Published',len(unique),'announced/verified offers; catalog coverage is not exhaustive')
if __name__=='__main__':main()
