import itertools
import lxml.html
import pybloomfilter
import re
import requests
import tldextract

from celery import Celery, group, task
from celery.utils.log import get_task_logger
from scraper.models import Page

logger = get_task_logger(__name__)

celery = Celery('tasks', backend='amqp', broker='amqp://guest@localhost//')


@task(name="app.tasks.crawl")
def crawl(start):
    """
    Starting from the specified url, crawl all urls on the same domain.
    """

    # Delete any page records in the database from a previous search
    Page.objects.all().delete()

    # Extract the domain and top level domain
    extract = tldextract.extract(start)
    domain = extract.domain
    tld = extract.tld

    # Use a bloom filter to keep track of urls which have been crawled.
    # This offers fast determination of set membership.  A negative result is
    # always correct but a positive result may be incorrent in which case a
    # page would not not be crawled.  This filter is sized to hold 100,000 
    # items with an error rate of less than .1 percent.
    crawled = pybloomfilter.BloomFilter(100000, 0.001, "/tmp/"+domain+tld)

    frontier = [start]

    # Until there are no more links to explore, search each url on the
    # frontier 'in parallel' and add any uncrawled links for the same domain
    # to the frontier for the next round.
    while frontier:
        logger.debug("Frontier {}\n".format(frontier))

        # Construct a list of scrape subtasks for each url on the
        # frontier  then mark each url as crawled and empty the frontier.
        tasks = [scrape.s(url, domain, tld) for url in frontier]
        crawled.update(frontier)
        frontier = []

        # Kick off all the searches at once and wait until they are all done
        # before proceeding.  The result is list of links found on each url.
        # No processing has been done so these lists may include duplicates and
        # non-http urls.
        result = group(tasks)()
        urls = result.get()
        logger.debug("Results {}\n\n".format(urls))

        # Join all the lists together and remove duplicates
        urls = set(itertools.chain.from_iterable(urls))

        # Filter out urls that have been called already or do not use http
        frontier = filter(lambda x: not x in crawled and
                          x.startswith('http://'), urls)

    return True

regex = re.compile(".*?on-sale")


@task(name="app.tasks.search_page")
def scrape(url, domain, tld):
    """
    Retrieve the page specified by the url, record in the database whether it
    contains the string "on-sale", and return a list of links on the page
    in the specified domain and top level domain.

    The list of links includes any duplicates that may be on the page.  Since
    the list will be processed further, there is no need to do extra work to
    filter them out here.

    The domain and tld arguments are redundant since that information is
    embedded in the url but it is faster to pass the information in that to
    recompute them for each url.
    """

    # In certain cases, when there is an error fetching the page, it may make
    # sense to retry but, for now, just log an error and return the empty
    # list.
    try:
        response = requests.get(url)
    except requests.exceptions.RequestException as err:
        logger.error("url {}: {}".format(url, err))
        return[]

    if response.status_code != 200:
        logger.error("url {}: status code {}".format(url, response.status_code))
        return []

    onsale = regex.search(response.text) is not None
    p = Page(url=url, onsale=onsale)
    p.save()

    # Parse the text of the page into a document and select the url in the
    # href for each a tag.  Then check whether it is in the specified domain
    # and top level domain.
    links = []
    dom = lxml.html.fromstring(response.text)
    for link in dom.xpath('//a/@href'):
        extract = tldextract.extract(link)
        if extract.domain == domain and extract.tld == tld:
            links.append(link)

    return links
