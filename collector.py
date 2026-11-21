"""Conservative deal collector: only publish explicitly dated, source-linked offers.

Configure permitted product pages in sources.json. Retailer blocking is reported, not bypassed.
Manual records in manual_deals.json must carry a source URL and verification timestamp.
"""
import json, pathlib, datetime, urllib.request, urllib.parse, re, html
from html.parser import HTMLParser
ROOT=pathlib.Path(__file__).resolve().parent
NOW=datetime.datetime.now(datetime.timezone.utc)
TODAY=NOW.date()
STORES=('target','kohls','walmart')
HOSTS={'target':('target.com',),'kohls':('kohls.com',),'walmart':('walmart.com',)}
class Scripts(HTMLParser):
 def __init__(self): super().__init__();self.in_json=False;self.buf='';self.scripts=[]
 def handle_starttag(self,tag,attrs):
  if tag=='script' and dict(attrs).get('type','').lower()=='application/ld+json':self.in_json=True;self.buf=''
 def handle_data(self,data):
  if self.in_json:self.buf+=data
 def handle_endtag(self,tag):
  if tag=='script' and self.in_json:self.scripts.append(self.buf);self.in_json=False

def allowed(url,store):
 try:
  u=urllib.parse.urlparse(url);return u.scheme=='https' and any(u.hostname==h or u.hostname.endswith('.'+h) for h in HOSTS[store])
 except Exception:return False

def walk(x):
 if isinstance(x,dict):
  yield x
  for v in x.values():yield from walk(v)
 elif isinstance(x,list):
  for v in x:yield from walk(v)

def fetch(url):
 req=urllib.request.Request(url,headers={'User-Agent':'FamilyDealRadar/1.0 (public product information; no authentication)','Accept':'text/html'})
 with urllib.request.urlopen(req,timeout=15) as res:return res.read(2_000_000).decode('utf-8','replace')

def collect(url,store):
 page=Scripts();page.feed(fetch(url))
 for s in page.scripts:
  try:obj=json.loads(html.unescape(s))
  except Exception:continue
  for item in walk(obj):
   typ=item.get('@type',[]);typ=[typ] if isinstance(typ,str) else typ
   if 'Product' not in typ:continue
   offers=item.get('offers') or {};offers=offers[0] if isinstance(offers,list) and offers else offers
   if not isinstance(offers,dict):continue
   # No inference of sale status from a product's ordinary price.
   start=offers.get('validFrom');end=offers.get('priceValidUntil')
   if not start or not end or not offers.get('price'):continue
   start=str(start)[:10];end=str(end)[:10]
   try:datetime.date.fromisoformat(start);datetime.date.fromisoformat(end)
   except ValueError:continue
   if end<TODAY.isoformat():continue
   yield {'id':f'{store}-{abs(hash(url))}', 'retailer':store,'title':str(item.get('name') or 'Product offer'), 'description':str(item.get('description') or '')[:400], 'category':str(item.get('category') or 'Other')[:80], 'sale_price':str(offers['price']), 'regular_price':None,'start_date':start,'end_date':end,'url':url,'cities':['all'],'availability':'Check retailer for local stock and pricing','verified':True,'verified_at':NOW.isoformat()}

def main():
 sources=json.loads((ROOT/'sources.json').read_text());manual=json.loads((ROOT/'manual_deals.json').read_text());deals=[];coverage={}
 for store in STORES:
  urls=sources.get(store,[]);issues=[];n=0
  for url in urls:
   if not allowed(url,store):issues.append('invalid or off-domain URL');continue
   try:
    items=list(collect(url,store));deals.extend(items);n+=len(items)
    if not items:issues.append('page has no explicit dated structured offers')
   except Exception as e:issues.append(type(e).__name__)
  coverage[store]={'status':f'{n} dated offers extracted; {len(issues)} source issues' if urls else 'no collector sources configured','pages_checked':len(urls),'issues':issues[:10]}
 for d in manual:
  store=d.get('retailer');url=d.get('url','')
  if store not in STORES or not allowed(url,store) or not d.get('verified_at') or not d.get('start_date') or not d.get('end_date'):continue
  try:
   verified=datetime.datetime.fromisoformat(d['verified_at'].replace('Z','+00:00'));end=datetime.date.fromisoformat(d['end_date']);datetime.date.fromisoformat(d['start_date'])
   if verified.tzinfo is None or NOW-verified>datetime.timedelta(days=3) or end<TODAY:continue
  except (ValueError,TypeError):continue
  if d.get('title') and d.get('cities') and d.get('verified') is True:deals.append(d)
 # Keep deterministic unique retailer + product + dates
 unique={ (d['retailer'],d['url'],d['start_date'],d['end_date']):d for d in deals }
 payload={'updated_at':NOW.isoformat(timespec='seconds'),'coverage':coverage,'deals':list(unique.values())}
 (ROOT/'deals.json').write_text(json.dumps(payload,indent=2,ensure_ascii=False)+'\n')
 print(f"Published {len(unique)} verifiable offers; coverage is not exhaustive")
if __name__=='__main__':main()
