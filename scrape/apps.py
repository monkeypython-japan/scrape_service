import os
from django.apps import AppConfig
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')  # 自分のsettings.py

# django.setup() # DEBUG for test from command line
# from registration.models import ScrapeTarget, ScrapeResult
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import threading
from datetime import datetime


def sign(x):
    return (x > 0) - (x < 0)

class ScrapeConfig(AppConfig):
    name = 'scrape'

    def resume_scraper(self):
        print(f'Im resume_scraper() {datetime.now()}')
        #test_concurrent()

    def ready(self):
        print('This is Scrape.ready()') # DEBUG
        controller = TaskController()
        INTERVAL_IN_SECOND = 600 # 10 minutes
        timer = RepeatTimer(controller.do_the_job, INTERVAL_IN_SECOND)
        timer.start_timer()   # comment out when use manage.py
        print('Exit Scrape.ready()') # DEBUG

class TimeSlot():
    def __init__(self, type, number):
        # Check parameters
        if type == 'H' and number in range(6):
            pass
        elif type == 'D' and number in range(24):
            pass
        elif type == 'W' and number in range(7):
            pass
        else:
            raise ValueError(f'Time_Slot_Spec_Error:{type}')
        # Parameters were OK. set to attributes
        self.type = type
        self.number = number

    def __str__(self):
        return self.type + str(self.number)

    def compare(self, other):
        return sign(self.number - other.number)


from django.utils import timezone
class TimeByTimeSlots():
   def __init__(self, dt=timezone.now()):
#   def __init__(self, dt=datetime.now()):  #DEBUG
        w = dt.weekday()
        h = dt.hour
        m = dt.minute // 10  # unitize by system base interval. current value is 10
        self.week_slot = TimeSlot('W', w)
        self.day_slot =  TimeSlot('D', h)
        self.hour_slot = TimeSlot('H', m)
        self.slot_list = [self.week_slot, self.day_slot, self.hour_slot]
        self.slot_dict = {'W':self.week_slot, 'D':self.day_slot, 'H':self.hour_slot}
        self.minutes_hour_slot = dt.minute
        self.minutes_day_slot = self.minutes_hour_slot + (h * 60)
        self.minutes_week_slot = self.minutes_day_slot + (w * 24 * 60)
        self.minutes_dict = {'W': self.minutes_week_slot, 'D': self.minutes_day_slot, 'H': self.minutes_hour_slot}
        self.total_minutes = self.minutes_week_slot

   def __str__(self):
       return str([str(s) for s in self.slot_list])

   def compare(self, other):
       return sign(self.total_minutes - other.total_minutes)

   def compare_within_slot(self,slot_letter,other):
        return sign(self.minutes_dict[slot_letter] - other.minutes_dict[slot_letter])

   def is_in_same_time_slot(self, slot_letter, other):
       if slot_letter == 'W':
           return self.week_slot.number == other.week_slot.number
       elif slot_letter =='D':
           return self.week_slot.number == other.week_slot.number and self.day_slot.number == other.day_slot.number
       elif slot_letter =='H':
           return self.week_slot.number == other.week_slot.number and self.day_slot.number == other.day_slot.number and self.hour_slot.number == other.hour_slot.number
       else:
           raise ValueError(f'Time_Slot_Spec_Error:{slot_letter}')


class RepeatTimer():
    ''' Execute a callable object with inetrval '''
    def __init__(self, callback, interval=60):
        '''
        :param callback: executable object to execute repeatedly
        :param interval: interval for execute in second
        '''
        # print(f'This is __init__() ') # DEBUG
        self.interval = interval
        self.callback = callback
        # print(f'__init__() {self.callback=}') # DEBUG

    def start_timer(self):
        ''' start to execute  '''
        #print(f'start_timer() {self.callback=}') # DEBUG
        self.callback()
        t = threading.Timer(self.interval, self.start_timer)
        #print(f'{timezone.now()}') #DEBUG
        #print(f'  {timezone.now().strftime('%Y/%d/%m %H:%M')}  ') #DEBUG
        t.start()


class TaskController():
    '''
    This class execute whole web scraping task baesed tasek defined in Database
    Instance pull task definition from DB with model ScrapeTarget.
    Execute scraping then write results to DB with ScrapeResult.
    This class use Tree data structure to minimize web page access
    Page access is executed with multithread. This minimize time to complete tasks.
    '''

    def __init__(self):
        MAX_WORKER = 2 # Max thread number for page access and scraping
        self.scheduler = Scheduler(MAX_WORKER)

    def fetch_single_task(self):
        ''' fetch URL, Xpath, target_pk from ScrapeTaregt '''
        pass

    def fetch_all_task(self):
        ''' fetch all URL, Xpath, target_pk from ScrapeTaregt'''
        # django.setup() # DEBUG for test from command line
        from registration.models import ScrapeTarget, ScrapeResult
        targets = ScrapeTarget.objects.all()
        return targets

    def fetch_tasks_for_current_interval(self):
        ''' fetch targets to be executed in current interval
            Treat all times after convert localtime in this method
        '''

        # django.setup() # DEBUG for test from command line
        from registration.models import ScrapeTarget, ScrapeResult
        from django.utils.timezone import localtime

        # current = TimeByTimeSlots()
        current = TimeByTimeSlots(localtime(timezone.now()))
        time_slots = current.slot_list
        results = []
        for slot in time_slots:
            type = slot.type
            number = slot.number
            hits = ScrapeTarget.objects.filter(interval = type, trigger_number = number)
            print(f'{type}{number} : {hits}') # DEBUG
            results.extend(hits)
        # Check if this task was done within this interval
        print(f'{results=}') # DEBUG
        for target in results:
            last_execution_time = None if target.last_execution_time is None else localtime(target.last_execution_time)
            #if last_execution_time is not None and current.compare_within_slot(target.interval, TimeByTimeSlots(last_execution_time)) == 1:
                # if last execution_time is pasted within specified interval time slot, task already executed in this interval
            if last_execution_time is not None and current.is_in_same_time_slot(target.interval, TimeByTimeSlots(last_execution_time)):
                # if last execution_time is in same time slot of current, task already executed in this interval
                print(f'Removed target:{target}') #DEBUG
                results.remove(target) #remove the target to pass execution
        print(f'Tasks for this interval:{results}') # DEBUG
        return results

    def build_task_tree(self):
        '''
        Build whole task tree with model ScrapeTarget
        '''
        task_tree = Tree()
        # targets = self.fetch_all_task() #DEBUG
        targets = self.fetch_tasks_for_current_interval()   # Select only targets match for this interval
        #print(f'{all_target=}') #DEBUG
        for target in targets:
            single_task_tree = Scraper.make_single_task(target.url, target.xpath, target.pk)
            #single_task_tree.describe() #DEBUG
            task_tree.graft_at_root(single_task_tree)
        task_tree.reduce()
        # task_tree.describe('build_task_tree()')  # DEBUG
        return task_tree

    def submit_single_url(self,url_node):
        '''
        submit single task to Scheduler
        args:
            url_node: (Node tha is root of task tree)
        '''
        scraper = Scraper()
        xpaths = url_node.names_of_children()
        url = url_node.name
        self.scheduler.submit(scraper.scrape_with_xpaths, url, url, xpaths )  #First url is key to result


    def execute_task_tree(self, task_tree):
        '''
        Execute all task in task tree
            args:
                task_tree: (Tree that contains all tasks to be execute in this interval)
            returns:
                Dictionary: {url:{xpath:value ...}, url2:{xpath:value...},...}
                value of the dictionary can be single error string
        '''
        url_nodes = task_tree.get_all_node_in_tear(1)  #Tear 1 contains ural nodes and subtree
        for url_node in url_nodes:
            self.submit_single_url(url_node) #Submit all url tasks

        results = self.scheduler.get_results()  # Wait for all task are done here
        return results    # {url:{xpath:value ...}, url2:{xpath:value...},...}


    def do_the_job(self):
        '''
        Top entry point to execute all tasks in this interval
        Fetch tasks from Database with model ScrapTarget, Submit all tasks and write result to db with model ScrapteResult
        '''
        # django.setup() # DEBUG for test from command line
        from registration.models import ScrapeTarget, ScrapeResult
        from django.utils import timezone
        from django.utils.timezone import localtime

        print(f'====== Start do_the_job() time:{localtime(timezone.now())}') #DEBUG
        task_tree = self.build_task_tree()

        #== executed in multiple threads. ==
        results = self.execute_task_tree(task_tree)
        #== return after all thread was done. ==

        for url, dict in results.items():
            #find url node in task tree
            url_dict = task_tree.root.children_as_dictionary() # tear 1 is url tear
            print(f'do_the_job() url:{url}  url_dict:{url_dict}') #DEBUG
            url_node = url_dict[url]
            xpath_dict = url_node.children_as_dictionary()
            for xpath, value in dict.items():
                #find xpath node and get it's target_pk nodes
                target_node = xpath_dict[xpath]
                target_pks = target_node.names_of_children()
                for target_pk in target_pks:
                    # Write value to DB ScrapeTarget with targete_pk
                    target = ScrapeTarget.objects.get(pk=target_pk)
                    result = ScrapeResult(target=target, time = timezone.now(), value = value)
                    print(f'{result=}') #DEBUG
                    target.last_execution_time = timezone.now()
                    result.save()
                    target.save()



class Scraper():
    '''
    Instance scrapes single page with multiple xPaths. Return multiple results.
    '''
    def scrape(self, url, xpath):
        '''
        Execute scrape with single xpath
        args:
            url: str target url
            xpath: str xpath of target in page
        return:
            first result of scraping
        '''
        return self.scrape_with_xpaths(url, [xpath])[xpath]

    def scrape_with_xpaths(self, url, xpaths):
        '''
         Execute scrape with multiple xpaths
         args:
             url: str target url
             xpaths: str list of xpath of target in page
         return:
             dict of result
             or
             str of Error Message
         '''
        import requests
        import lxml.html
        HEADERS = {'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.142 Safari/537.36'}
        TIMEOUT = 10
        results = {}
        try:
            response = requests.get(url, headers = HEADERS, timeout = TIMEOUT)
        except Exception as ex:
            error_message = str(ex)
            for xpath in xpaths:
                results[xpath] = '__SITE_ERROR__'
        else:
            #print(response.content) #DEBUG
            html = lxml.html.fromstring(response.content)
            for xpath in xpaths:
                tags = html.xpath(xpath)
                print(f'scrape_with_xpaths() tags:{tags}') #DEBUG
                results[xpath] = tags[0].text if len(tags) > 0 else '__NOVALUE__'

        return results

    @classmethod
    def make_single_task(cls, url, xpath, target_pk):
        '''
        Make task as single tree
        Args:
            url: (str  url to scrape
            xpath: (str xpath to target item)
            target_pk:  (int target_pk of task owner)
        Returns:
            single task as Tree
        '''
        root_node = Node('ROOT')
        url_node = Node(url)
        xpath_node = Node(xpath)
        #value_node = Node('VALUE')
        target_pk_node = Node(target_pk)
        #
        target_pk_node.add_to_parent(xpath_node)
        #value_node.add_to_parent(xpath_node)
        xpath_node.add_to_parent(url_node)
        url_node.add_to_parent(root_node)
        task_tree = Tree(root_node)
        return task_tree

class Scheduler():
    '''
    Instance executes functions with ThreadPoolExecutor
    '''
    def __init__(self,max_worker=1):
        '''

        Args:
            max_worker: int  maximum worker number

        Returns:
            get_results() returns all results of execution. this function blocks until finishing of all task
        '''
        self.max_worker = max_worker
        self.pool = ThreadPoolExecutor(self.max_worker)
        #self.pool = ProcessPoolExecutor(self.max_worker)
        self.futures = {}

    def submit(self, task, key, *args, **kwargs):
        '''
        Submit single task to Scheduler instance
        Args:
            task: callable object to be execute
            key: str  key for identify result
            *args:  args of task parameter
            **kwargs: kwargs of task pareameter

        '''
        future =  self.pool.submit(task, *args, **kwargs)
        #self.futures[key] = future
        self.futures[future] = key

    def get_results(self):
        '''
        Get results of tasks
        Returns:
            Dictionary of results of submited task.  Returns after all task is completed.
        '''
        import concurrent.futures
        results = {}
        for future in concurrent.futures.as_completed(self.futures):
            key = self.futures[future]
            try:
                result = future.result()
            except Exception as exc:
                print('%r generated an exception: %s' % (key, exc))
            else:
                results[key]=result
        self.futures = {}  #REMARK reset futures for next execution.
        return results # {key:result,...}

    def reset(self):
        '''
        Reset Scheduler instance to initial state
        '''
        self.pool = ThreadPoolExecutor(self.max_worker)
        #self.pool = ProcessPoolExecutor(self.max_worker)
        self.futures = {}

    def shutdown(self):
        '''
        Stop to execute tasks and reset
        '''
        self.pool.shutdown(True)
        self.reset()


class Node():
    '''
    Node class for component of Tree class
    '''
    def __init__(self,name, parent=None, children=None):
        '''
        Node has name, list of child and parent
        Args:
            name: node name
            parent: link to parent
            children: list of child node
        '''
        self.name = name
        self.parent = parent
        if not children:
            self.children = children
        else:
            self.children = None

    def add_child(self,child):
        '''
        Add single child to self
        Args:
            child: Node instance
        '''
        if self.children is None:
            self.children = []
        self.children.append(child)
        child.parent = self

    def add_to_parent(self,parent):
        '''
        Add self to sepcified node
        Args:
            parent: Node instance tobe added self
        '''
        parent.add_child(self)

    def is_leaf(self):
        '''
        Does instance have child?
        Returns:
            bool if this node is leaf or not
        '''
        return self.children is None

    def is_root(self):
        '''
        Is tnis node ROOT?
        Returns:
            bool if this node is ROOT or not?
        '''
        return self.parent is None

    def is_brohter_with(self, node):
        '''
        Judge if passed node is brother with self
        Args:
            node: node tobe judged

        Returns:
            bool if passed node is brother with self
        '''
        return self.parent == node.parent

    def merge(self, another_node):
        '''
        Move children of passed node to self children. passed node is modified.
        Args:
            another_node: Node instsnce to be merged
        '''
        # self.children.extend(another_node.children)
        for node in another_node.children:
            self.add_child(node)

    def distant_from_root(self,counter):
        '''
        Return distance between ROOT node and self.
        This function was impremented using recursive call. Counter should provide fromm outside.
        Args:
            counter: int  work variable for recursive call.

        Returns:
            int number of hop to instance
        '''
        if self.is_root():
            return counter
        else:
            counter += 1
            # print(f'{counter=}')
            return self.parent.distant_from_root(counter)

    def get_root(self):
        '''
        Find Root to traverse tree
        Returns:
            Node ROOT node instance
        '''
        if self.is_root():
            return self
        else:
            return self.parent.get_root()

    def get_all_descendant(self, container):
        '''
        Return list of decenent nodes of self.
        This function is impremented with recursive call. container should proveide from outside.
        Args:
            container: List to return results

        Returns:
            List of all decendent of self
        '''
        if self.children is not None:
            container.extend(self.children)
            for child in self.children:
                child.get_all_descendant(container)
        return container

    def remove_child(self, child):
        '''
        Remove a child from self's children
        Args:
            child: Node instance te be removed
        '''
        self.children.remove(child)
        child.parent = None

    def remove_self(self):
        '''
        Remove self from parent
        '''
        if self.parent is not None:   # if parent is None, this node is removed or root
            self.parent.remove_child(self)

    def names_of_children(self):
        '''
        Return list of names of children
        Returns:
            List of str
        '''
        if self.is_leaf():
            return []
        else:
            return [child.name for child in self.children]

    def children_as_dictionary(self):
        '''
        Return dictionary of child name and it self.
        Returns:
            dict of key: child name  value: Node instance
        '''
        return Node.make_dictionary(self.children) if self.children is not None else {}

    def __str__(self):
        childnun = len(self.children) if self.children is not None else 'Im a leaf'
        parentname = self.parent.name if self.parent is not None else 'Im the root'
        return \
            f'Node {self.name} root:{self.is_root()} leaf:{self.is_leaf()} Parent:{parentname} ChildrenNum:{childnun}'

    @classmethod
    def make_dictionary(cls,nodes):
        '''
        Make dictionary  from list of node
        Args:
            nodes: List of Node instances

        Returns:
            dict contains key:name of node  value:Node instance
        '''
        return {node.name : node for node in nodes}

    @classmethod
    def get_nodes_by_name(cls, name, nodes):
        '''
        Find node that named passed name
        Args:
            name: str  node name to be found
            nodes: List of Node instance

        Returns:
            List of Node instance
        '''
        results = []
        for node in nodes:
            if node.name == name:
                results.append(node)
        return results

class Tree():
    '''
    Tree class to hold tasks
    Tree is composed with Node instances
    '''
    def __init__(self,root=None):
        '''
        Make single tress that has only ROOT node
        Args:
            root:  Node instance to be ROOT
        '''
        if root is None:
            self.root = Node('ROOT')
        else:
            self.root = root

    def get_all_node_in_tear(self, tear):
        '''
        Get all nodes in passed tear.  ROOT is tear 0
        Args:
            tear: int  tear number

        Returns:
            List of Node instance
        '''
        if tear < 0:
            return []
        elif tear == 0:
            return [self.root]
        elif tear == 1:
            return self.root.children if self.root.children is not None else []  # children can be None
        else:
            merged = []
            for node in self.get_all_node_in_tear(tear -1):
                merged.extend(node.children)
            return merged

    def get_tear_as_dictionary(self,tear):
        '''
        Get all nodes in tear as dictionary
        Args:
            tear: int tear number   ROOT is tear 0

        Returns:
            dict of key:name of node   value: Node instance
        '''
        nodes = self.get_all_node_in_tear(tear)
        return Node.make_dictionary(nodes)

    def get_all_nodes(self):
        '''
        Get all node in self
        Returns:
            List of Node instance
        '''
        container = [self.root]
        return self.root.get_all_descendant(container)

    def get_depth(self):
        '''
        Return depath of self.  Root only tree's depath is 1
        Returns:
            int  depth of self
        '''
        depth = 0
        for node in self.get_all_nodes():
            counter = 0
            depth = max(depth, node.distant_from_root(counter))
        return depth + 1

    def get_shape(self):
        '''
        Retun list of node numbers that be contained in each tears
        First of list is always 1 because tear 0 contains only ROOT.
        Returns:
            list of int
        '''
        depth = self.get_depth()
        shape = []
        for tear in range(0,depth):
            shape.append(len(self.get_all_node_in_tear(tear)))
        return shape

    def reduce(self):
        '''
        Merge nodes that has same name and same parent into single node
        This operation minimize url access and scraping
        Modify self.
        '''
        depth = self.get_depth()
        if depth < 2:
            return
        for tear in range(1, depth): #Do every tear below 1
            #print(f'{tear=}') #DEBUG
            nodes = self.get_all_node_in_tear(tear)
            for node in nodes: # Do every node in this tear
                same_named_nodes = Node.get_nodes_by_name(node.name, nodes)
                for same_node in same_named_nodes: # Do every node that has same name
                    if same_node is not node and same_node.parent is node.parent:
                        #print(f'{same_node.name=}') #DEBUG
                        node.merge(same_node) # Merge chidren
                        same_node.remove_self()  # remove same_node from tree

    def graft_at_root(self,ather_tree):
        '''
        Graft passed tree to self's ROOT. This mean that ROOT of passed tree add to self as child.
        Args:
            ather_tree: Tree instance
        '''
        self.root.merge(ather_tree.root)

    def describe(self,comment=''):
        '''
        Print tree structre of self
        Returns:
            Print out to standard out
        '''
        print(f'------ START OF TREE ------- {comment}')
        depth = self.get_depth()
        for tear in range(0, depth):
            nodes = self.get_all_node_in_tear(tear)
            for node in nodes:
                print('({0}|<=|{1})'.format(node.parent.name if node.parent is not None else 'None',node.name),end='%%%')
            print(f'|END_OF_TEAR {tear}|')
        print(f'------- END OF TREE -------- {comment}')

    def __str__(self):
        return f'Tree root:{self.root.name} depth:{self.get_depth()} '


# ======
#  Test methods
# ======

def test_interval():
    import time
    from datetime import timedelta
    print('test_interval()')
    current_time = datetime.now()
    delta = timedelta(days=1, hours=1)
    future_time = current_time + delta
    past_time = current_time - delta

    current = TimeByTimeSlots(current_time)
    print(f'{current}')
    print(f'{current.total_minutes=}')
    print(f'{current.compare(current)=}')

    future = TimeByTimeSlots(future_time)
    print(f'{future}')
    print(f'{future.total_minutes=}')
    print(f'{current.compare(future)=}')

    past = TimeByTimeSlots(past_time)
    print(f'{past}')
    print(f'{past.total_minutes=}')
    print(f'{current.compare(past)=}')


def test_task_controller():
    print('test_task_controller()')
    controller = TaskController()
    controller.do_the_job()
    quit()

    task_tree = controller.build_task_tree()
    task_tree.describe() #DEBUG
    #quit()  #DEBUG

    url = 'https://m.finance.yahoo.co.jp/stock?code=998407.o'
    xpath = '//*[@id="detail-module"]/div/ul/li[1]/dl/dd'
    single_task_tree = Scraper.make_single_task(url, xpath, 1)
    single_task_tree.describe()
    result = controller.execute_task_tree(single_task_tree)
    print(f'{result=}')

def test_concurrent():
    print('test_concurrent()')
    scheduler = Scheduler(10)

    url1 = 'https://m.finance.yahoo.co.jp/stock?code=998407.o'
    xpath1 = '//*[@id="detail-module"]/div/ul/li[1]/dl/dd'

    url2 = 'https://stocks.finance.yahoo.co.jp/us/detail/TSLA'
    xpath2 = '//*[@id="main"]/div[3]/div/div[2]/table/tbody/tr/td[2]'
    #xpath2 = '/html/body/div/div[2]/div[2]/div[1]/div[3]/div/div[2]/table/tbody/tr/td[2]'

    #url3 = 'https://stocks.finance.yahoo.co.jp/stocks/detail/?code=7203.T'
    url3 = 'https://m.finance.yahoo.co.jp/stock?code=7203.T'
    #xpath3 = '//*[@id="stockinf"]/div[1]/div[2]/table/tbody/tr/td[2]'
    xpath3 = '//*[@id="detail-module"]/div[3]/ul/li[1]/dl/dd[1]'

    url4 = 'https://tenki.jp/forecast/3/14/4310/11208/'
    xpath4 = '//*[@id="main-column"]/section/div[1]/section[1]/div[1]/div[1]/p'
    xpath4 = '//*[@id="main-column"]/section/div[2]/section[1]/div[1]/div[1]/p'

    scraper = Scraper()
    print(f'{scraper.scrape(url1, xpath1)=}')
    print(f'{scraper.scrape(url2, xpath2)=}')
    print(f'{scraper.scrape(url3, xpath3)=}')
    print(f'{scraper.scrape(url4, xpath4)=}')

    scraper1 = Scraper()
    scheduler.submit(scraper1.scrape, url1, url1, xpath1)

    scraper2 = Scraper()
    scheduler.submit(scraper2.scrape, url2, url2, xpath2)

    scraper3 = Scraper()
    scheduler.submit(scraper3.scrape, url3, url3, xpath3)

    scraper4 = Scraper()
    scheduler.submit(scraper4.scrape, url4, url4, xpath4)

    #result = scheduler.futures[url].result(10)
    result = scheduler.get_results()  #Blcok until all task is completed
    print(f'{result=}')
    # print(results[xpath].encode('utf-8')) #DEBUG


def test_scrape():
    scraper = Scraper()
    #url = 'https://nikkei225jp.com/chart/'
    #xpath = '/html/body/div[1]/div/div[2]/div[1]/div/div[2]/div/table/tbody/tr[1]/td/div[1]/p'
    url = 'https://m.finance.yahoo.co.jp/stock?code=998407.o'
    #url = 'https://example.com'
    #xpath = '/html/body/div[4]/div[8]/div[2]/section[1]/div/div/ul/li[1]/dl/dd'
    xpath = '//*[@id="detail-module"]/div/ul/li[1]/dl/dd'
    text = scraper.scrape(url, xpath)
    print(f'{url=} {xpath=} {text=}')

    path_c = '//*[@id="detail-module"]/div/ul/li[3]/dl/dd'
    path_o = '//*[@id="detail-module"]/div/ul/li[4]/dl/dd'
    path_h = '//*[@id="detail-module"]/div/ul/li[5]/dl/dd'
    path_l = '//*[@id="detail-module"]/div/ul/li[6]/dl/dd'
    xpaths = [path_c, path_o, path_h, path_l]
    results = scraper.scrape_with_xpaths(url, xpaths)
    print( 'results: ', results)

 # Test Tree merge
def test_tree_merge():
    task1 = Scraper.make_single_task('https://www.sample.com','aaaaxxxxyyyybbbb','1234567')
    task2 = Scraper.make_single_task('https://www.google.com','zzzgggtttt','7878787878')
    task3 = Scraper.make_single_task('https://www.google.com',"<a ref>", "788889888")
    # print('task1:',task1)
    # print('Shape:',task1.get_shape())
    # print('task2:',task2)
    # print('Shape:',task2.get_shape())
    task1.graft_at_root(task2)
    task1.graft_at_root(task3)
    # task1.merge(task2)
    print('grafted task1:',task1)
    print('Shape:',task1.get_shape())
    task1.reduce()
    print('reduce task1:', task1)
    print('Shape:', task1.get_shape())
    task1.describe()
    quit()

# Test Tree and task
def test_tree():
    task = Scraper.make_single_task('https://www.sample.com','aaaaxxxxyyyybbbb','1234567')
    print(task)
    print('Tear 0:', task.get_all_node_in_tear(0)[0])
    print('Tear 1:', task.get_all_node_in_tear(1)[0])
    print('Tear 2:', task.get_all_node_in_tear(2)[0])
    print('Tear 3:', task.get_all_node_in_tear(3)[0])
    print('Tear 4:', task.get_all_node_in_tear(4)[0])
    print([str(node) for node in task.get_all_nodes()])
    # quit()

# Test Node & tree
def test_node():
    test_tree = Tree()
    print(test_tree)
    print(test_tree.root)
    #
    url_node = Node('URL1')
    print(url_node)
    xpath_node = Node('XPATH1',url_node)
    xpath_node.add_to_parent(url_node)
    xpath_node2 = Node('XPATH2',url_node)
    xpath_node2.add_to_parent(url_node)
    result_node = Node('Result',xpath_node)
    result_node.add_to_parent(xpath_node)
    result_node2 = Node('Result2', xpath_node)
    result_node2.add_to_parent(xpath_node2)

    print(url_node)
    print(xpath_node)
    print(xpath_node2)
    print(result_node)
    print(result_node2)
    print(f'Test get_root:{result_node2.get_root()}')
    counter = 0
    print(f'Test distant_from_root:{result_node2.distant_from_root(counter)}')
    container = []
    nodes = url_node.get_all_descendant(container)
    print(f'Test get_all_descendant():{nodes}')
    print(f'Test make_dictionary():{Node.make_dictionary(nodes)}')
    # quit()

def main():
    #
    test_interval()
    #print("Test scrape/apps.py")
    #test_task_controller()
    #test_interval()
    #test_concurrent()
    #test_scrape()
    # test_tree_merge()
    #quit()

if __name__ == "__main__":
    main()
