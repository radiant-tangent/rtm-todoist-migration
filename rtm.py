from rtmapi import Rtm
import os
from recurrent.event_parser import RecurringEvent
from datetime import datetime, timezone


class Task:
    def __init__(self, list_id=0, taskseries_id=0, task_id=0, text="", url="", tags=[], notes=[], repeat=None, date_due=None, parent_id=None, priority="PN", due_date_has_time=False):
        self.list_id = list_id
        self.taskseries_id = taskseries_id
        self.task_id = task_id
        self.text = text
        self.tags = self.convert_tags(tags)
        self.notes = self.convert_notes(notes)
        self.url = url
        self.repeat = self.convert_recur(repeat)
        self.date_due = self.convert_date(date_due, due_date_has_time)
        self.subtasks = []
        self.parent_id = int(parent_id) if parent_id is not None and len(parent_id) > 0 else 0
        self.priority = self.convert_proirity(priority)
    
    def __str__(self):
        return f"id: {self.task_id}, text: {self.text}, tags: {self.tags}, note_cnt: {len(self.notes)}, \
                recur: {self.recur}, subtask_cnt: {len(self.subtasks)}"

    def convert_proirity(self, priority):
        if "N" in priority:
            return 1
        elif '1' in priority:
            return 4
        elif '2' in priority:
            return 3
        elif '3' in priority:
            return 2
        return 1
    
    def convert_date(self, date, has_time=False):
        # get the date string in ISO format
        if date is None or (isinstance(date, str) and len(date) == 0):
            return date
        if isinstance(date, datetime):
            obj = date
        elif isinstance(date, str):
            obj = datetime.fromisoformat(date)
        else:
            obj = datetime.fromtimestamp(date/1000, timezone.utc)
        
        if has_time:
            return obj.isoformat()
        return obj.strftime("%Y-%m-%d")

    def convert_tags(self, tags):
        tag_str = ""
        if isinstance(tags, str):
            tag_str = tags
            
        elif isinstance(tags, list):
            tag_str = ','.join(tags)
        elif isinstance(tags, set):
            tag_str = ','.join(tags)
        else:
            tag_str = ','.join({t.value for t in tags})

        # remove any caracters emojies or non-ascii
        # tag_str = tag_str.encode('ascii', 'ignore').decode('ascii')

        return set(tag_str.split(','))


    def convert_notes(self, notes):
        if isinstance(notes, str):
            return [notes]
        elif isinstance(notes, list):
            return notes
        return [n.value for n in notes]
    
    def convert_recur(self, recur):
        if recur is None:
            return recur

        if isinstance(recur, str):
            if len(recur) == 0:
                return None
            rrule = "RRULE:"+recur
        else:        
            # Doesn't handle "after" rules
            if recur.every == '0':
                return None
            rrule = 'RRULE:'+recur.value
        
        
        human_string = RecurringEvent().format(rrule)

        # some clean up to make it more readable
        if "months" in human_string:
            every = human_string.index("every")
            end = human_string[every:]
            beginning = human_string[:every].replace(" of ", "")
            beginning = "on the " + beginning
            human_string = end + " " + beginning

        return {"rrule": rrule, "human": human_string}
    

class RTM:
    def __init__(self):
        self.api = self.get_api()

    def get_api(self):
        from dotenv import load_dotenv
        load_dotenv()
        api = Rtm(os.getenv('RTM_API_KEY'), os.getenv('RTM_SECRET'), "delete", os.getenv('RTM_TOKEN'), api_version=2)
        if not api.token_valid():
            # use desktop-type authentication
            url, frob = api.authenticate_desktop()
            # open webbrowser, wait until user authorized application
            # webbrowser.open(url)
            print("go to the following url to authenticate:")
            print(url)
            print('-------------')
            input("Continue?")
            # get the token for the frob
            api.retrieve_token(frob)
            # print out new token, should be used to initialize the Rtm object next time
            # (a real application should store the token somewhere)
            print("New token: %s" % api.token)
        return api

    def build_task(self, tl, ts):
        return Task(tl.id, ts.id, ts.task.id, ts.name, ts.url, ts.tags, ts.notes, ts.rrule, ts.task.due, ts.parent_task_id, ts.task.priority, ts.task.has_due_time == '1')

    def get_tasks(self, list_id=0, filter="", task_id=None):
        tasks = {}

        if list_id > 0 and len(filter.strip()) > 0:
            tskl = self.api.rtm.tasks.getList(list_id=str(list_id), filter=filter)
        elif list_id > 0:
            tskl = self.api.rtm.tasks.getList(list_id=str(list_id))
        elif len(filter.strip()) > 0:
            tskl = self.api.rtm.tasks.getList(filter=filter)
        else:
            tskl = self.api.rtm.tasks.getList()

        for tl in tskl.tasks:
            for ts in tl:
                if task_id is not None and ts.task.id != task_id:
                    continue
                tasks[str(ts.task.id)] = self.build_task(tl, ts)
        assoc_subtasks_to_parent(tasks)
        return tasks

    def get_all_tags(self):
        # each tag in the list has a tag.name
        return self.api.rtm.tags.getList().tags

    def get_all_lists(self):
        # each list in the list has
        # list.id, list.name,
        # indicators for deleted (0/1), locked (0,1), archive (0,1), position, smart(0/1)
        return self.api.rtm.lists.getList().lists

    def set_tags(self, task, tagset):
        timeline = self.api.rtm.timelines.create().timeline.value
        self.api.rtm.tasks.setTags(timeline=timeline, taskseries_id=task.taskseries_id,
                                   list_id=task.list_id, task_id=task.task_id, tags=','.join(tagset) if len(tagset) > 0 else "")

    def add_tags(self, task, tags_to_add):
        timeline = self.api.rtm.timelines.create().timeline.value
        self.api.rtm.tasks.addTags(timeline=timeline, taskseries_id=task.taskseries_id,
                                   list_id=task.list_id, task_id=task.task_id, tags=','.join(tags_to_add))

    def remove_tags(self, task, tags_to_remove):
        timeline = self.api.rtm.timelines.create().timeline.value
        self.api.rtm.tasks.removeTags(timeline=timeline, taskseries_id=task.taskseries_id,
                                      list_id=task.list_id, task_id=task.task_id, tags=','.join(tags_to_remove))

    def move_task(self, to_list_id, task):
        timeline = self.api.rtm.timelines.create().timeline.value
        self.api.rtm.tasks.moveTo(timeline=timeline, taskseries_id=task.taskseries_id,
                                  from_list_id=task.list_id, to_list_id=to_list_id, task_id=task.task_id)

    def update_task_name(self, task):
        timeline = self.api.rtm.timelines.create().timeline.value
        self.api.rtm.tasks.setName(timeline=timeline, taskseries_id=task.taskseries_id,
                                   list_id=task.list_id, task_id=task.task_id, name=task.text)

    def add_note_to_task(self, task, note):
        timeline = self.api.rtm.timelines.create().timeline.value
        self.api.rtm.tasks.notes.add(timeline=timeline, taskseries_id=task.taskseries_id,
                                     list_id=task.list_id, task_id=task.task_id, note_title="", note_text=note)

    def delete_task(self, task):
        timeline = self.api.rtm.timelines.create().timeline.value
        self.api.rtm.tasks.delete(timeline=timeline, taskseries_id=task.taskseries_id,
                                  list_id=task.list_id, task_id=task.task_id)
        

def assoc_subtasks_to_parent(tasks):
    for t in tasks.values():
        if t.parent_id > 0 and str(t.parent_id) in tasks:
            tasks[str(t.parent_id)].subtasks.append(str(t.task_id))
        elif t.parent_id > 0:
            print(f"Parent task {t.parent_id} not found for task {t.task_id}")

def build_task_from_json(task, notes):
    task_notes = []
    if task['series_id'] in notes:
        task_notes = notes[task['series_id']]
    return Task(task['list_id'], task['series_id'], task['id'], task['name'], 
                task['url'] if 'url' in task else '', task['tags'], task_notes, 
                task['repeat'] if 'repeat' in task else '', 
                task['date_due'] if 'date_due' in task else None, 
                task['parent_id'] if 'parent_id' in task else '',
                task["priority"] if "priority" in task else "PN",
                task["date_due_has_time"])

def get_tasks_from_export(filename):
    import json
    tasks = {}
    with open(filename, "r", encoding="utf-8") as f:
        data = json.load(f)

    notes = {}
    for note in data['notes']:
        notes[note['series_id']] = note['content']

    for task in data['tasks']:
        # get incomplete tasks only
        if "date_trashed" in task:
            continue
        if "date_completed" not in task:
            tasks[task['id']] = build_task_from_json(task, notes)

    assoc_subtasks_to_parent(tasks)

    return tasks

if __name__ == '__main__':
    
    # use json export
    tasks = get_tasks_from_export("/mnt/c/Users/username/Downloads/rtm_export.json")
    
    # use api
    tasks = RTM().get_tasks(filter="status:incomplete")
    pass