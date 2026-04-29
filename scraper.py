import re
from urllib.parse import urlparse, urldefrag, urljoin, urlencode, parse_qs

from bs4 import BeautifulSoup
from collections import Counter, defaultdict

KEEP_QUERY_PARAM = {'id', 'page_id', 'nid', 'dept', 'college', 'term', 'semester', 'year', 'people', 'p'}


stop_words = ['a', 'about', 'above', 'after','again','against','all','am','an','and','any','are','aren\'t','as',
                  'at','be','because','been','before','being','below','between','both','but','by','can\'t','cannot',
                  'could','couldn\'t','did','didn\'t','do','does','doesn\'t','doing','don\'t','down','during','each',
                  'few','for','from','further','had','hadn\'t','has','hasn\'t','have','haven\'t','having','he','he\'d',
                  'he\'ll','he\'s','her','here','here\'s','hers','herself','him','himself','his','how','how\'s','i',
                  'i\'d','i\'ll','i\'m','i\'ve','if','in','into','is','isn\'t','it','it\'s','its','itself','let\'s',
                  'me','more','most','mustn\'t','my','myself','no','nor','not','of','off','on','once','only','or','other',
                  'ought','our','ours','ourselves','out','over','own','same','shan\'t','she','she\'d','she\'ll','she\'s',
                  'should','shouldn\'t','so','some','such','than','that','that\'s','the','their','theirs','them',
                  'themselves','then','there','there\'s','these','they','they\'d','they\'ll','they\'re','they\'ve','this',
                  'those','through','to','too','under','until','up','very','was','wasn\'t','we','we\'d','we\'ll','we\'re',
                  'we\'ve','were','weren\'t','what','what\'s','when','when\'s','where','where\'s','which','while','who',
                  'who\'s','whom','why','why\'s','with','won\'t','would','wouldn\'t','you','you\'d','you\'ll','you\'re',
                  'you\'ve','your','yours','yourself', 'yourselves']

#currently not being printed anywhere.
unique_urls = set()
longest_page = 0
lp_url = ""
word_cnt = Counter()
subdomains = defaultdict(set) #would get one with longest length set at the end


def scraper(url, resp):
    links = extract_next_links(url, resp)
    return [link for link in links if is_valid(link)]

def extract_next_links(url, resp):
    # Implementation required.
    # url: the URL that was used to get the page
    # resp.url: the actual url of the page
    # resp.status: the status code returned by the server. 200 is OK, you got the page. Other numbers mean that there was some kind of problem.
    # resp.error: when status is not 200, you can check the error here, if needed.
    # resp.raw_response: this is where the page actually is. More specifically, the raw_response has two parts:
    #         resp.raw_response.url: the url, again
    #         resp.raw_response.content: the content of the page!
    # Return a list with the hyperlinks (as strings) scrapped from resp.raw_response.content
    global longest_page, lp_url, unique_urls, word_cnt, subdomains 

    if not resp:
        return []

    if not resp.status == 200:
        return [] 
    
    if not (resp.raw_response.url and resp.raw_response.content):
        return []
    
    url_c, fr = urldefrag(resp.raw_response.url)

    if url_c in unique_urls:
        return []
    unique_urls.add(url_c)

    soup = BeautifulSoup(resp.raw_response.content, "lxml")

    links = set()

    for tag in soup.find_all('a', href=True):
        absolute_link = safe_urljoin(url_c, tag['href'])
        if not absolute_link: continue

        new_url, frag = urldefrag(absolute_link)
        new_url = strip_bad_queries(new_url)

        if not (new_url in links):
            links.add(new_url)

    upd = urlparse(url_c).netloc.lower()
    subdomains[upd].add(url_c)

    all_text = soup.get_text(separator=' ', strip=True)
    ret_count, total = tokenize(all_text)

    if total > longest_page:
        lp_url = url_c
        longest_page = total

    word_cnt.update(ret_count)
    

    return list(links)

def is_valid(url):
    # Decide whether to crawl this url or not. 
    # If you decide to crawl it, return True; otherwise return False.
    # There are already some conditions that return False.
    try:
        url_c, fr = urldefrag(url)
        parsed = urlparse(url_c)

        if parsed.scheme not in set(["http", "https"]):
            return False
        
        dom = parsed.netloc.lower()

        if not (
            dom == 'ics.uci.edu' or dom.endswith('.ics.uci.edu')
            or dom == 'cs.uci.edu' or dom.endswith('.cs.uci.edu')
            or dom == 'informatics.uci.edu' or dom.endswith('.informatics.uci.edu')
            or dom == 'stat.uci.edu' or dom.endswith('.stat.uci.edu')
        ): return False

        #update these with more traps
        bad = ['ical=1', '/events/week', '/events/today', '/events/month', 'tribe__ecp_custom', ]

        if any (p in (parsed.path.lower() + '?' +  parsed.query.lower()) for p in bad):
            return False

        return not re.match(
            r".*\.(css|js|bmp|gif|jpe?g|ico"
            + r"|png|tiff?|mid|mp2|mp3|mp4"
            + r"|wav|avi|mov|mpeg|ram|m4v|mkv|ogg|ogv|pdf"
            + r"|ps|eps|tex|ppt|pptx|doc|docx|xls|xlsx|names"
            + r"|data|dat|exe|bz2|tar|msi|bin|7z|psd|dmg|iso"
            + r"|epub|dll|cnf|tgz|sha1"
            + r"|thmx|mso|arff|rtf|jar|csv"
            + r"|rm|smil|wmv|swf|wma|zip|rar|gz)$", parsed.path.lower())

    except TypeError:
        print ("TypeError for ", parsed)
        raise
    except Exception:
        return False

def tokenize(text):
    
    '''
    Reads in text file and returns a list of the tokens in that file. For the purposes of this project, 
    a token is a sequence of alphanumeric characters, independent of capitalization (so Apple, apple, aPpLe are the same token). 
    returns List<Token>
    '''
    
    tokens = re.findall(r"[a-z0-9]+", text.lower())
    total = len(tokens)
    counts = Counter(token for token in tokens if token not in stop_words)

    return counts, total


def safe_urljoin(url_c, tag):
    '''
    Safer version of urljoin to avoid exception.
    '''
    try:
        url = urljoin(url_c, tag)
        parsed = urlparse(url)
        if not parsed.scheme in {"http", "https"}: # checks for non http:
            return None
        if not parsed.netloc: # no domain + port
            return None

        return url

    except:
        return None

def strip_bad_queries(url):
    '''
    Given a url, this function strips query params not in KEEP_QUERY_PARAM
    '''
    parsed = urlparse(url)
    
    # Parse and filter query params
    params = parse_qs(parsed.query, keep_blank_values=False)
    filtered = {k: v for k, v in params.items() if k in KEEP_QUERY_PARAM}
    new_query = urlencode(sorted(filtered.items()), doseq=True)
    # Rebuild
    return parsed._replace(query=new_query).geturl()