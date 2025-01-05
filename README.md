# RememberTheMilk to Todoist Migration  

A utility to help migrate tasks from RememberTheMilk (RTM) to Todoist.
It is built with the following assumptions:

- RTM Lists are Todoist Projects (or Sections)
- RTM Tags are Todoist Labels
- RTM Notes are Todoist Comments
- A task URL from RTM will be added to the description for a task in Todoist
- Handles nested subtasks (up to 3 levels)
- Migrating to a Todoist with no tasks.  If you already have tasks, you may want to add an extra tag so that you can tell the old from the imported tasks.
- Priorities are the following:
  - RTM No Priority = Todoist normal priority (API=1; UI=4)
  - RTM Priority 3 = Todoist Priority 3 (API=2; UI=3)
  - RTM Priority 2 = Todoist Priority 2 (API=3; UI=2)
  - RTM Priority 1 = Todoist Priority 1 (urgent) (API=4; UI=1)

## Warning

- Does not handle recurrences well
  - This is mitigated by added the human readable recurrence text to the task name and adding a label of "fix-recurrance" to follow up on after import
- If a field isn't mentioned here, it is probably not handled in the migration.

## Getting Started

Data from RTM can be derived from a json export or use the RTM API. I can't help you set up auth for RTM API because I did it years ago; however, there is decent documentation on the [RTM API Documentation](https://www.rememberthemilk.com/services/api/authentication.rtm) site.

Make sure you have python installed. This was tested with Python 3.12.

Copy `.env.template` to `.env` and fill in your crendentials. The RTM credentials aren't needed if you are using a json export.

Create a python virtual environment `python3 -m venv .venv`

Activate the environment `source .venv/bin/activate`

Install the python dependencies `pip install -r requirements.txt`

To get a list of project and sections from todoist, run `Todoist().get_projects_and_sections()` from the `main()` function of `migrate.py`

To get a list of lists from RTM API run `RTM().get_all_lists()`

In `migrate.py`, update the `clists` dict to reflect your list mapping.  The keys are `list_id` strings from RTM and the values are tuples of `(Todoist project_id, Todoist section_id)`. If the list doesn't map to a section, use zero.

## Test a small data set

I recommend you start with a small sample of tasks to see if this will work well for you.  You can call `RTM().get_tasks()` with a `tag:tester` filter and use a test project in Todoist.

Note: Subtasks will not be returned with this filter unless they themselves also have the "tester" tag.

## Doing the full migration

To get tasks from an RTM Json export: `tasks = RTM().get_tasks_from_export("/path/to/export.json")`

To get tasks from the RTM API: `tasks = RTM().get_tasks(filter="status:incomplete")`

To import into Todoist: `Todoist().add_tasks(tasks)`

## References

- [Todoist REST API](https://developer.todoist.com/rest/v2/#overview)
- [Remember The Milk API](https://www.rememberthemilk.com/services/api/)