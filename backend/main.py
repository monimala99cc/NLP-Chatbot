from json.decoder import JSONObject
from fastapi.responses import JSONResponse
import db_helper
import generic_helper
from typing import Union
from fastapi import Request
from fastapi import FastAPI

app = FastAPI()

inprogress_orders = {}

@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.get("/items/{item_id}")
def read_item(item_id: int, q: Union[str, None] = None):
    return {"item_id": item_id, "q": q}

@app.post("/")
async def handle_request(request: Request):
    # Retrieve the JSON data from the request
    payload = await request.json()

    # Extract the necessary information from the payload
    # based on the structure of the WebhookRequest from Dialogflow
    intent = payload['queryResult']['intent']['displayName']
    parameters = payload['queryResult']['parameters']
    output_contexts = payload['queryResult']['outputContexts']
    session_id = generic_helper.extract_session_id(output_contexts[0]["name"])

    intent_handler_dict = {
        'order.add': add_to_order,
        'order.remove': remove_from_order,
        'order.complete': complete_order,
        'track.order - context: ongoing-tracking': track_order
    }

    return intent_handler_dict[intent](parameters, session_id)

def remove_from_order(parameters, session_id):
    #search the session id from inprogress dictionary to get the order
    #get the order dictionary {pizza:, Samosa:1, lassi:2}
    # get the food items from request remove pizza {pizza}
    # iterate the order dictionary and remove those food items

    if session_id not in inprogress_orders:
        fulfillmentText= "Sorry cant find your order. You need to place a new order"
    else:
        current_order = inprogress_orders[session_id]
        remove_items= parameters['food-item']
        items_removed=[]
        no_suchitems=[]
        for item in remove_items:
            if item in current_order:
                del current_order[item]
                items_removed.append(item)
            else:
                no_suchitems.append(item)

        if len(items_removed) > 0:
            fulfillment_text = f'Removed {",".join(items_removed)} from your order!'

        if len(no_suchitems) > 0:
            fulfillment_text = f' Your current order does not have {",".join(no_suchitems)}'

        if len(current_order.keys()) == 0:
            fulfillment_text += " Your order is empty!"
        else:
            order_str = generic_helper.get_str_from_food_dict(current_order)
            fulfillment_text += f" Here is what is left in your order: {order_str}. Anything else?"

        return JSONResponse(content={
            "fulfillmentText": fulfillment_text
        })

def track_order(parameters:dict,session_id: str):
    order_id= parameters['number']
    order_status= db_helper.get_order_status(order_id)
    if order_status:
        fulfillment_text = f"The order status for order id: {order_id} is: {order_status}"
    else:
        fulfillment_text = f"No order found with order id: {order_id}"
    print(fulfillment_text)
    return JSONResponse(content={
        "fulfillmentText": fulfillment_text
    })
def add_to_order(parameters: dict, session_id: str):
    print("Inside add_to_order")
    food_items = parameters["food-item"]
    quantities = parameters["number"]

    if len(food_items) != len(quantities):
        fulfillment_text = "Sorry I didn't understand. Can you please specify food items and quantities clearly?"
    else:
        new_food_dict = dict(zip(food_items, quantities))

        if session_id in inprogress_orders:
            current_food_dict = inprogress_orders[session_id]
            current_food_dict.update(new_food_dict)
            inprogress_orders[session_id] = current_food_dict
        else:
            print(new_food_dict)
            inprogress_orders[session_id] = new_food_dict

        order_str = generic_helper.get_str_from_food_dict(inprogress_orders[session_id])
        fulfillment_text = f"So far you have: {order_str}. Do you need anything else?"
    print(fulfillment_text)
    return JSONResponse(content={
        "fulfillmentText": fulfillment_text
    })

def complete_order(parameters: dict, session_id: str):
    if session_id not in inprogress_orders:
        fulfillmentText=f"There is some problem finding your order you need to place another order"
    else:
        order=inprogress_orders[session_id] #current order which needs to be saved in db
        order_id=save_to_db(order)
    if order_id == -1:
        fulfillment_text = "Sorry, I couldn't process your order due to a backend error. " \
                           "Please place a new order again"
    else:
        order_total = db_helper.get_total_order_price(order_id)

        fulfillment_text = f"Awesome. We have placed your order. " \
                           f"Here is your order id # {order_id}. " \
                           f"Your order total is {order_total} which you can pay at the time of delivery!"

    del inprogress_orders[session_id]

    return JSONResponse(content={
        "fulfillmentText": fulfillment_text
    })

def save_to_db(order):
    next_order_id=db_helper.get_next_order_id()
    # Insert individual items along with quantity in orders table
    for food_item, quantity in order.items():
        rcode = db_helper.insert_order_item(
            food_item,
            quantity,
            next_order_id
        )

        if rcode == -1:
            return -1

    # Now insert order tracking status
    db_helper.insert_order_tracking(next_order_id, "in progress")

    return next_order_id