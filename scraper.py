from datetime import date
import re
import os
from urllib.parse import urlparse, urldefrag, urljoin, parse_qs, urlencode

from bs4 import BeautifulSoup, XMLParsedAsHTMLWarning, MarkupResemblesLocatorWarning
from collections import Counter, defaultdict, deque

import hashlib, shelve, signal, sys, atexit, warnings
warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)
warnings.filterwarnings("ignore", category=MarkupResemblesLocatorWarning)

SHELF_PATH = "scraper.shelve"
BAD_QUERY = {'version', 'from', 'keywords', 'share', 'tribe-bar-date', 'rev', 'do', 'difftype', 'c', 'd', 'rev2[]', 'ns', 'tab_details', 'tab_files', 'image', 'can_fetch', 'idx', 'action', 'format'}
HASH_BITS = 64 # Bits in a given hash
SIMILAR_THRESHOLD = .9 # Pages that are similar by 90% are considered near-identica pages.
PAGES_BTWN_UPDATE = 100
SIZE_LIMIT = 1 * 1024 * 1024


stop_words = {
    "a", "able", "about", "above", "abst", "accordance", "according", "accordingly", "across", "act", "actually", "added", "adj", "affected", "affecting", "affects",
    "after", "afterwards", "again", "against", "ah", "all", "almost", "alone", "along", "already", "also", "although", "always", "am", "among", "amongst", 
    "an", "and", "announce", "another", "any", "anybody", "anyhow", "anymore", "anyone", "anything", "anyway", "anyways", "anywhere", "apparently",
    "approximately", "are", "aren", "arent", "arise", "around", "as", "aside", "ask", "asking", "at", "auth", "available", "away", "awfully", "b", "back",
    "be", "became", "because", "become", "becomes", "becoming", "been", "before", "beforehand", "begin", "beginning", "beginnings", "begins", "behind", "being",
    "believe", "below", "beside", "besides", "between", "beyond", "biol", "both", "brief", "briefly", "but", "by", "c", "ca", "came", "can", "cannot", "can't",
    "cause", "causes", "certain", "certainly", "co", "com", "come", "comes", "contain", "containing", "contains", "could", "couldnt", "d", "date", "did",
    "didn't", "different", "do", "does", "doesn't", "doing", "done", "don't", "down", "downwards", "due", "during", "e", "each", "ed", "edu", "effect",
    "eg", "eight", "eighty", "either", "else", "elsewhere", "end", "ending", "enough", "especially", "et", "et-al", "etc", "even", "ever", "every", "everybody", "everyone", "everything", "everywhere", "ex", "except", "f",
    "far", "few", "ff", "fifth", "first", "five", "fix", "followed", "following", "follows", "for", "former", "formerly", "forth", "found", "four", "from","further", "furthermore", "g", "gave", "get", "gets", "getting", "give",
    "given", "gives", "giving", "go", "goes", "gone", "got", "gotten", "h", "had", "happens", "hardly", "has", "hasn't", "have", "haven't", "having", "he", "hed", "hence", "her", "here", "hereafter", "hereby", "herein",
    "heres", "hereupon", "hers", "herself", "hes", "hi", "hid", "him","himself", "his", "hither", "home", "how", "howbeit", "however", "hundred", "i", "id", "ie", "if", "i'll", "im", "immediate", "immediately",
    "importance", "important", "in", "inc", "indeed", "index", "information", "instead", "into", "invention", "inward", "is", "isn't", "it", "itd", "it'll", "its", "itself", "i've", "j", "just", "k", "keep", "keeps",
    "kept", "kg", "km", "know", "known", "knows", "l", "largely", "last", "lately", "later", "latter", "latterly", "least", "less", "lest", "let", "lets", "like", "liked", "likely", "line", "little", "'ll", "look",
    "looking", "looks", "ltd", "m", "made", "mainly", "make", "makes", "many","may", "maybe", "me", "mean", "means", "meantime", "meanwhile", "merely", "mg", "might", "million", "miss", "ml", "more", "moreover", "most",
    "mostly", "mr", "mrs", "much", "mug", "must", "my", "myself", "n", "na", "name", "namely", "nay", "nd", "near", "nearly", "necessarily", "necessary", "need", "needs", "neither", "never", "nevertheless", "new", "next", "nine",
    "ninety", "no", "nobody", "non", "none", "nonetheless", "noone", "nor", "normally", "nos", "not", "noted", "nothing", "now", "nowhere", "o", "obtain", "obtained", "obviously", "of", "off", "often", "oh", "ok",
    "okay", "old", "omitted", "on", "once", "one", "ones", "only", "onto", "or", "ord", "other", "others", "otherwise", "ought", "our", "ours",
    "ourselves", "out", "outside", "over", "overall", "owing", "own", "p",  "page", "pages", "part", "particular", "particularly", "past", "per",
    "perhaps", "placed", "please", "plus", "poorly", "possible", "possibly", "potentially", "pp", "predominantly", "present", "previously", "primarily", "probably", "promptly", "proud", "provides", "put", "q",
    "que", "quickly", "quite", "qv", "r", "ran", "rather", "rd", "re","readily", "really", "recent", "recently", "ref", "refs", "regarding","regardless", "regards", "related", "relatively", "research",
    "respectively", "resulted", "resulting", "results", "right", "run", "s", "said", "same", "saw", "say", "saying", "says", "sec", "section", "see",
    "seeing", "seem", "seemed", "seeming", "seems", "seen", "self", "selves","sent", "seven", "several", "shall", "she", "shed", "she'll", "shes",
    "should", "shouldn't", "show", "showed", "shown", "showns", "shows",  "significant", "significantly", "similar", "similarly", "since", "six",
    "slightly", "so", "some", "somebody", "somehow", "someone", "somethan", "something", "sometime", "sometimes", "somewhat", "somewhere", "soon",  "sorry", "specifically", "specified", "specify", "specifying", "still",
    "stop", "strongly", "sub", "substantially", "successfully", "such", "sufficiently", "suggest", "sup", "sure", "t", "take", "taken", "taking", "tell", "tends", "th", "than", "thank", "thanks", "thanx", "that",
    "that'll", "thats", "that've", "the", "their", "theirs", "them", "themselves", "then", "thence", "there", "thereafter", "thereby", "thered", "therefore", "therein", "there'll", "thereof", "therere", "theres", 
    "thereto", "thereupon", "there've", "these", "they", "theyd", "they'll", "theyre", "they've", "think", "this", "those", "thou", "though", "thoughh", "thousand", "throug", "through", "throughout", "thru", "thus",
    "til", "tip", "to", "together", "too", "took", "toward", "towards", "tried", "tries", "truly", "try", "trying", "ts", "twice", "two", "u", "un", "under", "unfortunately", "unless", "unlike", "unlikely", "until",
    "unto", "up", "upon", "ups", "us", "use", "used", "useful", "usefully", "usefulness", "uses", "using", "usually", "v", "value", "various", "'ve", "very", "via", "viz", "vol", "vols", "vs", "w", "want", "wants", "was",
    "wasnt", "way", "we", "wed", "welcome", "we'll", "went", "were", "werent", "we've", "what", "whatever", "what'll", "whats", "when", "whence", "whenever", "where", "whereafter", "whereas", "whereby", "wherein",
    "wheres", "whereupon", "wherever", "whether", "which", "while", "whim", "whither", "who", "whod", "whoever", "whole", "who'll", "whom", "whomever", "whos", "whose", "why", "widely", "willing", "wish", "with",
    "within", "without", "wont", "words", "world", "would", "wouldnt", "www", "x", "y", "yes", "yet", "you", "youd", "you'll", "your", "youre", "yours", "yourself", "yourselves", "you've", "z", "zero",
    "1","2","3","4","5","6","7","8","9","0"
}

with shelve.open(SHELF_PATH) as db:
    unique_urls  = db.get('unique_urls',  set())
    longest_page = db.get('longest_page', 0)
    lp_url       = db.get('lp_url',       '')
    word_cnt     = db.get('word_cnt',     Counter())
    subdomains   = db.get('subdomains',   defaultdict(int))
    hash_cache   = db.get('hash_cache',   deque(maxlen=5000))

def update_shelf():
    global longest_page, lp_url, unique_urls, word_cnt, subdomains
    with shelve.open(SHELF_PATH) as db:
        unique_urls  = db.get('unique_urls',  set())
        longest_page = db.get('longest_page', 0)
        lp_url       = db.get('lp_url',       '')
        word_cnt     = db.get('word_cnt',     Counter())
        subdomains   = db.get('subdomains',   defaultdict(int))
        hash_cache   = db.get('hash_cache',   deque(maxlen=5000))

def save_shelf():
    with shelve.open(SHELF_PATH) as db:
        db['unique_urls']   = unique_urls
        db['longest_page']  = longest_page
        db['lp_url']        = lp_url
        db['word_cnt']      = word_cnt
        db['subdomains']    = subdomains
        db['hash_cache']   = hash_cache

def update_stats():
    save_shelf()
    temp = "output.txt.tmp"
    fin = "output.txt"

    with open(temp, "w") as outFile:
        outFile.write(f"Number of unique pages: {len(unique_urls)}\n")  # Using f-strings (Python 3.6+)
        outFile.write("Longest page: " + str(lp_url) + f", with {longest_page} words.\n")

        outFile.write("Top 50 words:\n")
        top_50 = word_cnt.most_common(50)
        for word, count in top_50:
           outFile.write(f"{word}: {count}\n")

        outFile.write("\nSubdomains and the number unique pages detected:\n")
        for url, sub in sorted(subdomains.items()):
            outFile.write(f"{url}, {sub}\n")

    os.replace(temp, fin)

def handle_interrupt(signum, frame):
    print("\nSaving state...")
    update_stats()
    sys.exit(0)

signal.signal(signal.SIGINT,  handle_interrupt)
signal.signal(signal.SIGTERM, handle_interrupt)
atexit.register(update_stats)

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

    if resp.status >= 600:
        if not valid_cache_status(resp.status):
            return []

    if not resp.status == 200:
        return [] 
    
    if not (resp.raw_response and resp.raw_response.url and resp.raw_response.content):
        return []

    if is_too_large(resp):
        return []
    
    # Duplicate Check
    url_c, fr = urldefrag(resp.raw_response.url)
    if url_c in unique_urls:
        return []
    if not is_valid(url_c):
        return []

    # Content Processing
    soup = BeautifulSoup(resp.raw_response.content, "lxml")
    all_text = soup.get_text(separator=' ', strip=True)
    ret_count, total = tokenize(all_text)

    # Similarity Check
    if is_similar(ret_count):
        unique_urls.add(url_c)
        upd = urlparse(url_c).netloc.lower()
        subdomains[upd] += 1
        return []

    # Data Logging
    unique_urls.add(url_c)
    upd = urlparse(url_c).netloc.lower()
    subdomains[upd] += 1

    if total > longest_page:
        lp_url = url_c
        longest_page = total

    word_cnt.update(ret_count)
    if len(word_cnt) > 10000:
        word_cnt = Counter(dict(word_cnt.most_common(2500))) # remove 7500 least common words to save memory

    # Link Extraction
    links = set()
    for tag in soup.find_all('a', href=True):
        absolute_link = safe_urljoin(url_c, tag['href'])
        if not absolute_link: continue

        new_url, frag = urldefrag(absolute_link)
        new_url = strip_bad_queries(new_url)

        links.add(new_url)

    
    
    if len(unique_urls) % PAGES_BTWN_UPDATE == 0:
        update_stats()

    return links

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
        bad = ['ical=1', '/events/week', '/events/today', '/events/month', 'tribe__ecp_custom','login',
            '/pix/', '/families/', '/junkyard/', '/pubs/', '/twist/', # Block large datasets
            'do=diff', 'do=media', 'do=edit', 'do=export', # Block Wiki actions
            'share=', 'format=xml', 'action=download',      # Block file exports
            'ical=1', 'calendar', 'events'                  # Block infinite calendars
        ]

        # matches dates in the format YYYY-MM-DD or YYYY/MM/DD
        date_pattern = re.compile(r'\d{4}[-/]\d{2}[-/]\d{2}') 
        if date_pattern.search(parsed.path):
            return False

        if any (p in (parsed.path.lower() + '?' +  parsed.query.lower()) for p in bad):
            return False

        return not re.match(
            r".*\.(css|js|bmp|gif|jpe?g|ico|img|json"
            + r"|png|tiff?|mid|mp2|mp3|mp4"
            + r"|wav|avi|mov|mpeg|ram|m4v|mkv|ogg|ogv|pdf"
            + r"|ps|eps|tex|ppt|pptx|doc|docx|xls|xlsx|names"
            + r"|data|dat|exe|bz2|tar|msi|bin|7z|psd|dmg|iso"
            + r"|epub|dll|cnf|tgz|sha1"
            + r"|thmx|mso|arff|rtf|jar|csv|lif"
            + r"|c|cpp|py|ipynb|h|java|apk"
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
    Given a url, this function strips query params in BAN_QUERY_PARAMS 
    and returns the cleaned url. 
    This is to avoid crawling the same page with different 
    query params that don't change the content.
    '''
    parsed = urlparse(url)
    
    # Parse and filter query params
    params = parse_qs(parsed.query, keep_blank_values=False)


    filtered = {k: v for k, v in params.items() if k.lower() not in BAD_QUERY}
    new_query = urlencode(sorted(filtered.items()), doseq=True)
    # Rebuild
    return parsed._replace(query=new_query).geturl()

def hashify(token):
    '''
    Hash a token to a hash value. We use this instead of Python's built-in hash function because this is determinstic.
    '''
    return int(hashlib.md5(token.encode('utf-8')).hexdigest(), 16)

def sim_hash(word_count: Counter):
    '''
    Given the word count, returns the SimHash of the page.
    '''
    bit_vector = [0] * HASH_BITS
    for token, weight in word_count.items():
        mask = 1
        hash_token = hashify(token)
        for i in range(HASH_BITS):
            if hash_token & mask:
                bit_vector[i] += weight
            else:
                bit_vector[i] -= weight
            mask <<= 1

    sim = 0
    mask = 1
    for i in range(HASH_BITS):
        if bit_vector[i] > 0:
            sim |= mask
        mask <<= 1
    
    return sim

def sim_hash_compare(sim_hash1, sim_hash2, threshold):
    '''
    Compares the 2 simhash and returns True if it meets the threshold and is similar, else False.
    '''
    x = sim_hash1 ^ sim_hash2
    diff_bits = x.bit_count()
    return (1 - diff_bits / HASH_BITS) > threshold

def is_similar(word_count: Counter):
    '''
    Determines if a page is similar to previous pages based on word_count.
    '''
    sim = sim_hash(word_count)
    for other_hash in hash_cache:
        if sim_hash_compare(sim, other_hash, SIMILAR_THRESHOLD):
            return True
    hash_cache.append(sim)
    return False

def is_exact(size):
    '''
    Determines if a page is exact.
    '''
    # This function will match the size for all sizes of the webpages. If it is an exact match, it will return true.
    # We will not be using this, since we have similarity check.
    return size in sizes # sizes would be a set of all previous sizes, but we won't have that, replaced by simhash.

def is_too_large(resp):
    '''
    Determines if a page is too large.
    '''
    content_length = resp.raw_response.headers.get('Content-Length')
    if content_length and int(content_length) > SIZE_LIMIT:
        return True
    return len(resp.raw_response.content) > SIZE_LIMIT

def valid_cache_status(status):
    match status:
        case 600: # request malformed
            raise Exception("Status 600: request is malformed")
        case 601: # failed download, skip
            return False
        case 602: # bad server, skip
            return False
        case 603: # incorrect http/https
            raise Exception("Status 603: Not http or https")
        case 604: # Bad domain, skip
            return False
        case 605: # bad file extension, skip
            return False
        case 606: # Bad parsing
            return Exception("Status 606: Exception in parsin")
        case 607: # Content too big, allow in for handling
            return True
        case 608: # Denied by domain robot rules, skip
            return False