from dotenv import load_dotenv
import json
import os
from todoist_api_python.api import TodoistAPI
from rtm import RTM


# convert from RTM list to Todolist project and section
clists = {
    "46234599": (2342345667, 0),
    "46146709": (2327786314, 0),
    "50279404": (2346234494, 0),
    "46513798": (2346234467, 178234392),
    "46572568": (2222346665, 0),
    "46515601": (2341234567, 178565416),
    "46512603": (2349844237, 0),
    "46385178": (2656778967, 178234653)
}


class Todoist:
    def __init__(self):
        load_dotenv()
        self.api = TodoistAPI(os.environ["TODOIST_API_KEY"])

    def print_itemss(self, title, items):
        print(f"--- {title} ---")
        for i in items:
            print(f"Item: {i.name} - ID: {i.id}")

    def get_projects_and_sections(self):
        try:
            projects = self.api.get_projects()
            sections = self.api.get_sections()
            self.print_itemss("Projects", projects)
            self.print_itemss("Sections", sections)
        except Exception as error:
            print(error)

    def add_task(self, task, tasks, parent_id=None):
        project, section = clists[str(task.list_id)]
        params = {}
        
        if len(task.url) > 0:
            params["description"] = task.url
        if len(task.date_due) > 10:
            params["due_datetime"] = task.date_due
        elif len(task.date_due) > 0:
            params["due_date"] = task.date_due
        params["priority"] = task.priority
        if project > 0:
            params["project_id"] = str(project)
        if section > 0:
            params["section_id"] = str(section)
        content = task.text
        labels = list(task.tags)
        if task.repeat:
            content = content + " " + task.repeat["human"]
            labels.append("fix-recurrance")
        params["content"] = content
        params["labels"] = labels
        if parent_id:
            params["parent_id"] = parent_id

        
        try:
            new_task = self.api.add_task(**params)
        except Exception as error:
            print(error)
        new_task_id = new_task.id
        for note in task.notes:
            try:
                comment = self.api.add_comment(
                    content=note,
                    task_id=new_task_id,
                )
            except Exception as error:
                print(error)
        for subtask in task.subtasks:
            self.add_task(tasks[subtask], tasks, new_task_id)


    def add_tasks(self, tasks):
        for id, task in tasks.items():
            # skip subtasks bc they'll be created when parent task is created
            if task.parent_id > 0:
                continue
            self.add_task(task, tasks)    

def main():
    load_dotenv()
    tasks = RTM().get_tasks(filter="status:incomplete")
    Todoist().add_tasks(tasks)

if __name__ == '__main__':
    main()