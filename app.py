import os
import random, string
# Use the package we installed
from slack_bolt import App, Say

from slack_bolt.adapter.socket_mode import SocketModeHandler

from auth.mongo import db

from datetime import date

import requests

import json

# Initialize your app with your bot token and signing secret
app = App(token=os.environ.get("SLACK_BOT_TOKEN"))

def main():
   handler = SocketModeHandler(app, os.environ.get("SLACK_APP_TOKEN"))
   handler.start()


def guest_home_view(client,event, logger, context):
    try:
      # views.publish is the method that your app uses to push a view to the Home tab
      client.views_publish(
          # the user that opened your app's app home
          user_id=context['user_id'],
          view = {
            "type": "home",
            "callback_id": "guest_home_view",
            "blocks": [
              {
                "type": "header",
                "text": {
                  "type": "plain_text",
                  "text": "Task Management App Home",
                  "emoji": True
                }
              },
              {
                "type": "divider"
              },
              {
                "type": "section",
                "text": {
                  "type": "mrkdwn",
                  "text": "Click the Login button to start using TM App"
                },
                "accessory": {
                  "type": "button",
                  "text": {
                    "type": "plain_text",
                    "text": "Login",
                    "emoji": True
                  },
                  "style": "primary",
                  "value": "login_button",
                  "action_id": "login-button-action"
                }
              }
            ]
          }
        )
    except Exception as e:
      logger.error(f"Error publishing home tab: {e}")

# Login button Modal

@app.action("login-button-action")
def open_login_modal(ack, body, logger, context, client):
    ack()
    logger.info(body)
    try:
        # Call the views.open method using the WebClient passed to listeners
        client.views_open(
          trigger_id=body["trigger_id"],
          view={
            "callback_id": "login_view",
            "title": {
              "type": "plain_text",
              "text": "Login",
              "emoji": True
            },
            "submit": {
              "type": "plain_text",
              "text": "Login",
              "emoji": True
            },
            "type": "modal",
            "close": {
              "type": "plain_text",
              "text": "Cancel",
              "emoji": True
            },
            "blocks": [
              {
                  "type": "section",
                  "block_id": "user_name_details",
                  "text": {
                      "type": "mrkdwn",
                      "text": f"Username: *{context['user_id']}*"
                  }
              },
              {
                "type": "input",
                "block_id": "password_details",
                "element": {
                  "type": "plain_text_input",
                  "action_id": "user_password",
                  "placeholder": {
                    "type": "plain_text",
                    "text": "Password"
                  }
                },
                "label": {
                  "type": "plain_text",
                  "text": "Password",
                  "emoji": True
                }
              }
            ]
          }
        )
    except Exception as e:
      logger.error(f"Error publishing home tab: {e}")

# Handle login data 

# Handle a view_submission request
@app.view("login_view")
def handle_submission(ack, body, client, context, view, payload, logger):
    ack()
    view_data = view["state"]["values"]
    data = {
      "username": context['user_id'],
      "password": view_data ["password_details"]["user_password"]["value"]
    }
    result = requests.post('http://127.0.0.1:5000/user/login', json=data)
    print(data)
    print("--------------------------------------------")
    print(payload)
    print("--------------------------------------------")
    user_result = result.json()

    tokens = db['token']

    tokenData = {
        'workspace': payload["team_id"],
        'user': context['user_id'],
        'salt': user_result["salt"]
    }
    tokens.insert_one(tokenData)
    errors = {}
    if len(errors) > 0:
        ack(response_action="errors", errors=errors)
        return
    
    update_home_tab(client, context, logger)


def check_token(context):
    tokens = db['token']
    result = tokens.find_one({'user': context["user_id"]})
    print(result)
    if result and result["salt"] != None :
        print(result["salt"])
        return True
    return False


#Update App Home

def update_home_tab(client, context, logger):
  try:
    # Get the all tasks 
    response = requests.get('http://127.0.0.1:5000/tasks')
    tasks_length = None
    if response.status_code == 200:
      #print(response.json())
      tasks = response.json()[0]
      tasks_length = len(response.json()[0])
      print(tasks_length)
      #print(tasks)
      if(tasks_length > 0):
        tasks_block = []
        for task in tasks:
          print(task)
          tasks_block.append(
              {
                "type": "section",
                "text": {
                  "type": "plain_text",
                  "text": task["title"],
                  "emoji": True
                }
              }
          )
          tasks_block.append(
            {
                "type": "actions",
                "elements": [
                  {
                    "type": "button",
                    "text": {
                      "type": "plain_text",
                      "text": "Edit",
                      "emoji": True
                    },
                    "value": task["id"],
                    "action_id": "actionId-0"
                  },
                  {
                    "type": "button",
                    "text": {
                      "type": "plain_text",
                      "text": "Delete",
                      "emoji": True
                    },
                    "style": "danger",
                    "value": task["id"],
                    "action_id": "actionId-1"
                  }
                ]
              }
          )
        home_blocks = [
          {
            "type": "header",
            "text": {
              "type": "plain_text",
              "text": "Task Management App Home",
              "emoji": True
            }
          },
          {
            "type": "divider"
          },
          {
            "type": "actions",
            "elements": [
              {
                "type": "button",
                "text": {
                  "type": "plain_text",
                  "text": "Create a task",
                  "emoji": True
                },
                "value": "create_a_task",
                "action_id": "create_new_task"
              },
              {
                "type": "button",
                "text": {
                  "type": "plain_text",
                  "text": "Create a project",
                  "emoji": True
                },
                "value": "create_a_project",
                "action_id": "create_project"
              },
              {
                "type": "button",
                "text": {
                  "type": "plain_text",
                  "text": "Join a project",
                  "emoji": True
                },
                "value": "join_a_project",
                "action_id": "join_project"
              },
              {
                "type": "button",
                "text": {
                  "type": "plain_text",
                  "text": "Invite a member",
                  "emoji": True
                },
                "value": "add_a_member",
                "action_id": "add_member"
              }
            ]
          },
          {
            "type": "divider"
          },
          {
            "type": "actions",
            "elements": [
              {
                "type": "button",
                "text": {
                  "type": "plain_text",
                  "text": "My Tasks"
                },
                "style": "primary",
                "value": "my_tasks"
              },
              {
                "type": "button",
                "text": {
                  "type": "plain_text",
                  "text": "To Do"
                },
                "value": "todo_tasks"
              },
              {
                "type": "button",
                "text": {
                  "type": "plain_text",
                  "text": "In Progress"
                },
                "value": "inprogress_tasks"
              },
              {
                "type": "button",
                "text": {
                  "type": "plain_text",
                  "text": "Completed Tasks"
                },
                "value": "completed_tasks"
              }
            ]
          },
          {
            "type": "divider"
          }
        ]
        home_blocks.extend(tasks_block)
      else:
        home_blocks = [
          {
            "type": "section",
            "text": {
              "type": "plain_text",
              "text": "You have not created any task yet, Please click on 'Create a task' button and create your first task.",
              "emoji": True
            }
          },
          {
            "type": "divider"
          },
          {
            "type": "actions",
            "elements": [
              {
                "type": "button",
                "text": {
                  "type": "plain_text",
                  "text": "Create a task",
                  "emoji": True
                },
                "value": "create_a_task",
                "action_id": "create_new_task"
              },
              {
                "type": "button",
                "text": {
                  "type": "plain_text",
                  "text": "Create a project",
                  "emoji": True
                },
                "value": "create_a_project",
                "action_id": "create_project"
              },
              {
                "type": "button",
                "text": {
                  "type": "plain_text",
                  "text": "Join a project",
                  "emoji": True
                },
                "value": "join_a_project",
                "action_id": "join_project"
              },
              {
                "type": "button",
                "text": {
                  "type": "plain_text",
                  "text": "Invite a member",
                  "emoji": True
                },
                "value": "add_a_member",
                "action_id": "add_member"
              }
            ]
          }
        ]
    else:
      raise Exception(f"Non-success status code: {response.status_code}")

    #print(home_blocks)
    # views.publish is the method that your app uses to push a view to the Home tab
    client.views_publish(
      # the user that opened your app's app home
      user_id=context["user_id"],
      # the view object that appears in the app home
      view={
        "type": "home",
        "callback_id": "home_view",
        "blocks" : home_blocks
        # body of the view
        
      }
    )

  except Exception as e:
    logger.error(f"Error publishing home tab: {e}")

@app.event("app_home_opened")
def show_home_tab_conditionaly(client, context, logger):
  if check_token(context) : 
     #print("Amit")
     update_home_tab(client, context, logger)
  else:
     guest_home_view(client, context, logger, context)

# @app.shortcut("new_task")
# def open_modal(ack, shortcut, client, logger):
#     # Acknowledge shortcut request
#     ack()

#     try:
#         # Call the views.open method using the WebClient passed to listeners
#         result = client.views_open(
#             trigger_id=shortcut["trigger_id"],
#             view={
#                 "type": "modal",
#                 "title": {"type": "plain_text", "text": "My App"},
#                 "close": {"type": "plain_text", "text": "Close"},
#                 "blocks": [
#                   {
#                       "type": "section",
#                       "text": {
#                           "type": "mrkdwn",
#                           "text": "Create task the simplest modal.",
#                       },
#                   }
#                 ],
#             },
#         )
#         logger.info(result)

#     except Exception as e:
#         logger.error("Error creating conversation: {}".format(e))

@app.action("create_new_task")
def create_new_task (ack, logger, body, client):
    logger.info(f"request body: {body}")
    ack()
    try:
        # Call the views.open method using the WebClient passed to listeners
        result = client.views_open(
            trigger_id=body["trigger_id"],
            view={
              "type": "modal",
              "callback_id": "create_task_view",
              "title": {
                "type": "plain_text",
                "text": "Create new task",
                "emoji": True
              },
              "submit": {
                "type": "plain_text",
                "text": "Submit",
                "emoji": True
              },
              "close": {
                "type": "plain_text",
                "text": "Cancel",
                "emoji": True
              },
              "blocks": [
                {
                  "type": "divider"
                },
                {
                  "type": "input",
                  "element": {
                      "type": "plain_text_input",
                      "action_id": "input_task_title_action",
                      "placeholder": {
                          "type": "plain_text",
                          "text": "Task title"
                      }
                  },
                  "block_id": "input_task_title",
                  "label": {
                      "type": "plain_text",
                      "text": "Task Title"
                  }
                },
                {
                  "type": "input",
                  "block_id": "input_task_details",
                  "element": {
                    "type": "rich_text_input",
                    "action_id": "input_task_details-action"
                  },
                  "label": {
                    "type": "plain_text",
                    "text": "Task Description",
                    "emoji": True
                  }
                },
                {
                  "type": "input",
                  "block_id": "input_date_block",
                  "element": {
                    "type": "datepicker",
                    "initial_date": date.today().isoformat(),
                    "placeholder": {
                      "type": "plain_text",
                      "text": "Select a due date",
                      "emoji": True
                    },
                    "action_id": "due_date_selector"
                  },
                  "label": {
                    "type": "plain_text",
                    "text": "Due date",
                    "emoji": True
                  }
                }
              ]
            }
        )
        logger.info(result)

    except Exception as e:
        logger.error("Error creating conversation: {}".format(e))


@app.view("create_task_view")
def handle_create_task_events(ack, body, context, client, view, logger, say:Say):
    ack()
    logger.info(body)
    data = view["state"]["values"]
    print(data)
    new_data = {
      "id": "12345",
      "title": data["input_task_title"]["input_task_title_action"]["value"],
      "description": data["input_task_details"]["input_task_details-action"]["rich_text_value"]["elements"][0]["elements"][0]["text"],
      "status": "TODO",
      "dueDate": data["input_date_block"]["due_date_selector"]["selected_date"]
    }
    print(new_data)
    requests.post('http://127.0.0.1:5000/tasks', json=new_data)
    update_home_tab(client, context, logger)

# # Handle a view_submission request
# @app.view("create_task_view")
# def handle_create_task_events(ack, body, context, client, view, logger, say:Say):
#     ack()
#     data = view["state"]["values"]
#     print(data)
#     new_data = {
#         "id": "12345",
#         "title": data["input_task_title"]["input_task_title_action"]["value"],
#         "description": data["input_task_details"]["input_task_details-action"]["rich_text_value"],
#         "status": "TODO",
#         "dueDate": "10/05/2024",
#         "assigneeUserName": body["user"]["id"]
#     }
#     #user = body["user"]["id"]
    # request_dat= requests.post('http://127.0.0.1:5000/tasks', json=new_data)
    # #print(user)
    # #print(data)
    # #print(context)
    # # Validate the inputs
    # errors = {}
    # if len(errors) > 0:
    #     ack(response_action="errors", errors=errors)
    #     return
    
    # say(channel=context["user_id"], text="Task created successfully")
    # update_home_tab(client, context, logger)
    # logger.info(body)


@app.action("actionId-1")
def delete_task_action(ack, body, logger, payload, context, say, client):
    ack()
    logger.info(body)
    #print(payload["value"])
    requests.delete(f'http://127.0.0.1:5000/tasks/{payload["value"]}')

    say(channel=body["user"]["id"], text="Task deleted successfully")

    update_home_tab(client, context, logger)

#def create_your_first_task () : 
   

@app.action("actionId-0")
def edit_task(ack, body, client, logger, payload):
    ack()
    try:
        # Call the views.open method using the WebClient passed to listeners
        result = client.views_open(
            trigger_id=body["trigger_id"],
            view={
              "type": "modal",
              "callback_id": "update_task_view",
              "title": {
                "type": "plain_text",
                "text": "Update task",
                "emoji": True
              },
              "private_metadata": payload["value"],
              "submit": {
                "type": "plain_text",
                "text": "Update",
                "emoji": True
              },
              "close": {
                "type": "plain_text",
                "text": "Cancel",
                "emoji": True
              },
              "blocks": [
                {
                  "type": "divider"
                },
                {
                  "type": "input",
                  "block_id": "update_input_task",
                  "element": {
                    "type": "plain_text_input",
                    "action_id": "update_task_details-action"
                  },
                  "label": {
                    "type": "plain_text",
                    "text": "New task",
                    "emoji": True
                  }
                },
                {
                  "type": "input",
                  "block_id": "update_user_id",
                  "element": {
                    "type": "multi_users_select",
                    "placeholder": {
                      "type": "plain_text",
                      "text": "Select users",
                      "emoji": True
                    },
                    "action_id": "multi_users_select-action"
                  },
                  "label": {
                    "type": "plain_text",
                    "text": "Assign user",
                    "emoji": True
                  }
                }
              ]
            }
        )
        logger.info(result)

    except Exception as e:
        logger.error("Error creating conversation: {}".format(e))

@app.view("update_task_view")
def update_task(ack, body, logger, payload, say, view, client, context):
    ack()
    logger.info(body)
    print(view["private_metadata"])
    model_data = body["view"]["state"]["values"]
    print(model_data["update_input_task"]["update_task_details-action"]["value"])
    print(model_data["update_user_id"]["multi_users_select-action"]["selected_users"][0])
    #print(model_data["selected_users"])
    data = {
        "assignee": model_data["update_user_id"]["multi_users_select-action"]["selected_users"][0],
        "description": model_data["update_input_task"]["update_task_details-action"]["value"],
        "status": "DONE"
    }
    print(data)
    requests.put(f'http://127.0.0.1:5000/tasks/{view["private_metadata"]}', json=data)

    say(channel=body["user"]["id"], text="Task updated successfully")

    update_home_tab(client, context, logger)


@app.action("create_project")
def handle_create_project_action(ack, body, logger, client):
    ack()
    print("C P Working")
    try:
        # Call the views.open method using the WebClient passed to listeners
        print("Try working")
        client.views_open(
          trigger_id=body["trigger_id"],
          view={
            "type": "modal",
            "callback_id": "create_project_channel",
            "title": {
              "type": "plain_text",
              "text": "Create Project",
              "emoji": True
            },
            "submit": {
              "type": "plain_text",
              "text": "Submit",
              "emoji": True
            },
            "close": {
              "type": "plain_text",
              "text": "Cancel",
              "emoji": True
            },
            "blocks": [
              {
                "type": "input",
                "block_id": "project_name",
                "element": {
                  "type": "plain_text_input",
                  "action_id": "project_name_input-action"
                },
                "label": {
                  "type": "plain_text",
                  "text": "Project name",
                  "emoji": True
                }
              },
              {
                "type": "input",
                "block_id": "project_description",
                "element": {
                  "type": "plain_text_input",
                  "multiline": True,
                  "action_id": "project_description_input-action"
                },
                "label": {
                  "type": "plain_text",
                  "text": "Project description",
                  "emoji": True
                }
              },
              {
                "type": "input",
                "block_id": "select_project_manager_block",
                "element": {
                  "type": "multi_users_select",
                  "placeholder": {
                    "type": "plain_text",
                    "text": "Select users",
                    "emoji": True
                  },
                  "action_id": "select_project_manager"
                },
                "label": {
                  "type": "plain_text",
                  "text": "Select project manager ",
                  "emoji": True
                },
                "hint": {
                  "type": "plain_text",
                  "text": "Select 1 project manager",
                  "emoji": True
                }
              },
              {
                "type": "input",
                "block_id": "select_dev_block",
                "element": {
                  "type": "multi_users_select",
                  "placeholder": {
                    "type": "plain_text",
                    "text": "Select users",
                    "emoji": True
                  },
                  "action_id": "select_project_dev"
                },
                "label": {
                  "type": "plain_text",
                  "text": "Select developers",
                  "emoji": True
                },
                "hint": {
                  "type": "plain_text",
                  "text": "Select 1 or more developers",
                  "emoji": True
                }
              },
              {
                "type": "input",
                "block_id": "select_qa_block",
                "element": {
                  "type": "multi_users_select",
                  "placeholder": {
                    "type": "plain_text",
                    "text": "Select users",
                    "emoji": True
                  },
                  "action_id": "select_project_qa"
                },
                "label": {
                  "type": "plain_text",
                  "text": "Select QA",
                  "emoji": True
                },
                "hint": {
                  "type": "plain_text",
                  "text": "Select 1 or more QA",
                  "emoji": True
                }
              }
            ]
          }
        )
        logger.info(body)
    except Exception as e:
      logger.error("Error creating conversation: {}".format(e))

@app.view("create_project_channel")
def handle_create_channel_events(ack, body, logger, view, client):
    ack()
    logger.info(body)
    view_data = view["state"]["values"]
    print(view_data)
    project_name = view_data['project_name']['project_name_input-action']['value']
    channel_name = project_name.replace(" ", "-")
    pm_user = view_data['select_project_manager_block']['select_project_manager']['selected_users']
    dev_user = view_data['select_dev_block']['select_project_dev']['selected_users']
    qa_user = view_data['select_qa_block']['select_project_qa']['selected_users']
    users = []
    users.extend(pm_user)
    users.extend(dev_user)
    users.extend(qa_user)

    print(users)

    #client.conversations_create(name=channel)
    #client.conversations_invite(channel)
    channel = client.conversations_create(name=channel_name, is_private=False)
    #print(channel)
    #print(channel['channel']['id'])
    #print(channel['channel']['name'])
    client.conversations_invite(channel=channel['channel']['id'], users=users)
    # for user in users:
    #   user_data = client.users_profile_get(user)
    #   print('Amit-----------')
    #   print(user_data)

    # client.chat_postMessage(
    #     channel=channel['channel']['id'], 
    #     text=f"Welcome to {users['id']}"
    # )
    # print(client)

## Add member functionality

@app.action("add_member")
def handle_add_member(ack, body, logger, client):
    ack()
    logger.info(body)
    client.views_open(
      trigger_id=body["trigger_id"],
      view={
        "type": "modal",
        "callback_id": "add_a_member_cb",
        "title": {
          "type": "plain_text",
          "text": "Invite a member",
          "emoji": True
        },
        "submit": {
          "type": "plain_text",
          "text": "Invite",
          "emoji": True
        },
        "close": {
          "type": "plain_text",
          "text": "Cancel",
          "emoji": True
        },
        "blocks": [
          {
            "type": "input",
            "block_id": "input_user_id",
            "element": {
              "type": "plain_text_input",
              "action_id": "input_user_id-action"
            },
            "label": {
              "type": "plain_text",
              "text": "User ID",
              "emoji": True
            },
            "hint": {
              "type": "plain_text",
              "text": "Enter a user id , Ex - U06UPCWJDAM",
              "emoji": True
            }
          },
          {
            "type": "input",
            "block_id": "select_user_role",
            "element": {
              "type": "static_select",
              "placeholder": {
                "type": "plain_text",
                "text": "Select an item",
                "emoji": True
              },
              "options": [
                {
                  "text": {
                    "type": "plain_text",
                    "text": "PM",
                    "emoji": True
                  },
                  "value": "PM"
                },
                {
                  "text": {
                    "type": "plain_text",
                    "text": "DEV",
                    "emoji": True
                  },
                  "value": "DEV"
                },
                {
                  "text": {
                    "type": "plain_text",
                    "text": "QA",
                    "emoji": True
                  },
                  "value": "QA"
                }
              ],
              "action_id": "select-role-action"
            },
            "label": {
              "type": "plain_text",
              "text": "Role",
              "emoji": True
            }
          }
        ]
      }
    )

@app.shortcut("invite_member")
def invite_member(ack, body, logger, client):
   handle_add_member(ack, body, logger, client)

@app.view("add_a_member_cb")
def handle_add_member_events(ack, body, logger, view, context, say):
    ack()
    logger.info(body)
    view_data = view["state"]["values"]
    password = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
    project_joining_code = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
    data = {
      "username": view_data ["input_user_id"]["input_user_id-action"]["value"],
      "password": password,
      "role": view_data ["select_user_role"]["select-role-action"]["selected_option"]["value"]
    }
    requests.post('http://127.0.0.1:5000/user/signup', json=data)
    say(channel=context["user_id"], text=f"New member details : username : {data["username"]} , password : {data["password"]}, Joining Code : {project_joining_code}")

# Ready? Start your app!
if __name__ == "__main__":
  main()

