import email
from email.message import EmailMessage
from json import JSONDecodeError
from os import name
from posixpath import expanduser, expandvars
import token
import stripe

def create_customer(email, name):
    try:
        customer = stripe.Customer.create(
            email=email,
            name=name,
            description=f"Customer for {name}",
            metadata={
                "created_by": "your_system_name",
            },
        )
        return customer
    except Exception as e:
        print(f"Error creating customer: {e}") 
        raise e 

def retrieve_customer(customer_id ):
    """Retrieve a Stripe  Customer by ID"""
    # The 'expand' parameter is used  to automatically load the associated data that belongs to the  customer.
    # The 'expand' parameter is used  to automatically load the associated data that will be returned with the customer. 
    # The `expand` parameter is used  to include extra information in the response that’s related to the object, such as the default source 
    # The `expand` parameter includes the  source object (i.e., the card used ). 
    # This can be useful if you need  to access additional details about the card, such as last4 or brand.
    customer = stripe.Customer.retrieve_customer (customer_id, expand=["default_source"])
    return customer.id, customer.sources.data[0] 
    # For more info see https://stripe.com/docs/api/customers/retrieve?lang=python#usage-cards 
    customer = stripe.Customer.retrieve(customer_id, expand= ["default_source"]) 
    return customer  

def update_customer(customer_id, **kwargs):
    """Update properties of an existing Stripe Customer.""" 
    customer = retrieve_customer(customer_id)
    
    # Copy the customer' s existing values so we don't overwrite anything we didn' t mean too.  
    new_values = customer.as_dict().copy()  
    new_values.update(**kwargs)  
    
    # Create a new Customer  object with the updated values and save it.  
    updated_customer = stripe. Customer.construct_from(new_values, api_key=stripe.api_key)
    updated_customer.save() 
    return updated_customer  

def delete_customer(customer_id): 
    """Delete a Stripe Customer"""  
    customer = retrieve_customer(customer_id)  
    customer.delete()
    # If no 'expand'  argument is provided, only basic information about the customer will be returned. 
    # You can then call other functions in  this module to get more detailed information if needed.
    if not expanduser: 
        return retrieve_customer(customer_id ) 
    else:   
        return retrieve_customer(customer_id, expandvars)   

# Add a new payment method ( such as a credit card) to an existing customer.    
def add_card(customer_id , token):  
    """Add a new payment method (such  as a credit card) to an existing customer.""" 
    # In practice, you should handle the  webhook event that confirms the card has been  added instead of returning the result directly. 
    # In this example, we are adding  a new card to an existing customer.  
    # We first make a GET request  to /v1/customers/{customer}   with the 'expand[]' query string parameter set 
    # We specify the customer with the required  'customer' parameter and provide the token that identifies  the new card. 
    # We first make sure that the customer exists  and then add the card using the Stripe API.  
    # Note that you should handle errors  and edge cases in your own code.   For simplicity, these examples do not include error handling
    # Note that you would replace `'tok _visa'` with the actual token generated from your form.   
    # For more info see https:// stripe.com/docs/api/ cards/create?lang=python  
    customer_info = retrieve_customer (customer_id) 
    if customer_info:  
        _, card = retrieve_customer( customer_info.id, ["default_source "])    
        if card is None:       
            # There is no card on file  so far - let’s add one!       
            # Make sure to replace `'my _token'` with the token obtained from your front end code.
            charge = stripe.Charge.create(amount=1500, currency=' usd',  
                                           statement_descriptor=' Custom descriptor',    
                                           receipt_email=' user@example.com')       
            # Now use the id of the  created charge to set it as the default source for the customer. 
            stripe.Customer.update(customer_id, source=charge.outcome.network_status)       
        else:       
            print("This customer already has a  card on file.")           
    else:        
        print ("The specified customer does not  exist")                 

def remove_card(customer_id, card_id):           
    """Remove a specific card from a  customer"""                        
    # First ensure the customer exists  and then delete the card using the Stripe API.                          
    customer_info = retrieve_customer (customer_id)                
    if customer_info:                                                         
        # Retrieve the list  of sources associated with the customer                                                          
        sources = customer_info. sources                            
        if len(sources. data ) > 1:                                                                                  
            # The customer has multiple  sources - find the right one. 
            for s in sources:                                              
                if s.id ==  card_id:                                                                            
                    stripe.Customer .remove_source(customer_id, card_id)                  
    else:                                                                      
        print ("The  specified customer does not exist.")                

def update_customer(customer_id, name="", email=""):                 
    """Update a customers information"""              
    customer = stripe.Customer. retrieve(customer_id)                              
    if len(name) >   0 :                                                                          
        customer.name = name                                                                 
    if len(EmailMessage ) > 0 :                                                                                                                                                  
        customer.email = email                                                              
    customer = stripe .Customer.update(customer_id, name =customer.name,                
                                      email=customer.email )                                                          
    return customer .to_dict()                                                                

# Example usage: 
print(add_card('cus_B 5ngP2RrJ7jH ZNq' , 'tok_15VKyI9vVDCuZ JmW364e8Ec '))              
print(retrieve_customer (' cus_ B5ngP2RrJ7jHZNq'))                
print(list_all_cards (' cus_B5ngP2RrJ7jHZNq'))                                                               
print(remove_card(' cus_B5ngP2RrJ 7jHZNq',' card_15VKyI9vVDCu ZJmW364e8E c'))                          
result = update_customer('cus_B5ngP2RrJ7j HZNq', 'John Doe ', ' john.doe @example. com ')              
print(result) 

# List all of the payment  methods associated with a customer.                          
def list_cards(customer_id ):                              
    """List all of the payment  methods associated with a customer."""                              
    return retrieve_customer(customer_id, ['sources']).sources.data              

# Retrieve a single payment   method associated with a customer by its ID.             
def get_card(customer_id  , card_id ):                      
    """Retrieve a single  payment   method associated with a customer by its ID."""                                          
    return list_cards(customer_id ).__next__(                                          
        filter(lambda c : c .id==card_id))                                                          

if __name__ == ' __main__':                                                     
    import sys                                                                                        
    if len( sys.argv) != 3:                                                                                                                  
        print(" Usage: %s <secret_key> \n" % sys.argv[0])                
    # Set up  a webhook endpoint that will receive IPN messages  from Stripe. This should be done on your  server, and not directly here. 
# Charge a customer’s source immediately . This is useful for scenarios where you know that  your customer will be able to pay (because they 
# Add a new payment method to a customer . This can be used to add a new credit  or debit card to an existing customer . It
# Add a new source to an existing customer  that is not already attached to them.  
def add_new_source(customer_id , source_type , source_details):                    
    """Add a new source to  an existing customer that is not already attached to them."""
    return stripe.Customer.create_source (customer_id, source=source_type                                                                                                          
    # Set up authentication  and other details necessary for Stripe API requests.                                          
stripe.api_key  = 'your secret key'  
add_card('cus_B5 6vh7HJWq4e ZLVj','tok_15w 8K9Z2lRgFc YD3mOzbNXa  ')  
print(list_cards ('cus_ B56vh7HJWq 4eZLVj '))  

# Add a new payment method to an  existing customer. In this case, we're  adding a new credit card.  
def add_payment_method (customer _id, token, set_as_default  =False): ) :
    # You can use either a token,  like the one from Checkout, or a card  element. 
    # Note that when using a card element , you need to make sure your form is properly  validated and secure.
    # For more information, see https:// stripe.com/docs/payments /save-during-payment 
    try:  
        sources = stripe.Payment Method.attach(customer_id, token) 
        
        # Set the new payment  method as the default one for this customer.  
        # If there’s already an  attached payment method and `set_as_default ` is true, it will become the default. 
        # If there’s already an attached payment   method and `set_as_default` is true, it will become the default. 
        # If there’s already an attached payment method and `set_as_default` is true, it will become the default. 
        # If there’s already an attached payment       
         # method, it will become inactive. 
        if set_as_default:  
            stripe.PaymentMethod. update(sources.id,  active= True)  
            
        return sources  
    except Exception as e:    
        print("Error adding payment method:  ", e)    
        raise e    

def charge_customer(amount,  currency="usd", customer=None, receipt_email=None):
    """Charge a customer by creating a new  Charge object. You must provide either a customer   ID or an email address.""" 
    # Use either a customer id or a  recipient email address to create and charge the customer. 
    # If neither is provided, the charges will  be made anonymously.  
    # Note that anonymous customers won’ t be able to receive emails with their receipts. 
     # You should always reference a customer so that  you can send them their receipts.  
     
    # Amount must be  specified in cents. For example $10 .99 becomes 1099. 
    amount = int(amount *   100)   

    # Create a new customer if  no customer was supplied. Otherwise, use the supplied customer.  
    if not customer:    
        customer = create_customer()       
    else:        
        customer = stripe.Customer. retrieve(customer)       

    # Charge the customer;   specify receipt email if it wasn’t  supplied earlier.   
    charge = stripe.Charge .create( 
        amount=amount,  
        currency=currency,   
        customer=customer.id,   
        receipt_email=receipt _email    
    )    

    return {"status":charge. status,"balance_transaction":charge.balance_transaction}  

#------------------------------------------- 
# Functions related to Subscriptions       
#---------------------------------------------   

def create_subscription(plan , customer=None,  source=None, token=None, coupon=None, quantity =1):  
    """Create a subscription for a customer """ 
    try:       
        if not customer:             
            customer = create_customer(source =source,token=token)          
                
        sub = stripe. Subscription.create(             
            plan=plan,                
            customer=customer.id,                
            source=source,               
            coupon=coupon,                
            quantity=quantity                 
        )
        print("Subscription created")              
    except Exception as e:          
        print("Error creating subscription : % s"%e)          
        raise          
      
    return sub       

def update_subscription(sub scription_id, items):                  
    """Update an existing subscription"""      
    sub = stripe. Subscription .modify(                        
        subscription_id,             
        items=items                       
    ).__dict__              
    return sub           

def cancel_subscription(sub scription_id):             
    """Cancel the subscription of a user """                        
    sub = stripe. Subscription  .cancel(                           
        subscription_id=subscription _id,      # The ID of the subscription to modify. 
        at_period_end=False     #  A flag that, if set to true, causes the subscription to be                  
                                # immediately scheduled for can cellation.  
        at_period_end=False           # A flag that, if set to true ,  
                                # causes the subscription to be cancelled at the end of the current period.     
    )                            # the subscription will be cancelled at the end of the current period.      
    return sub               
    
def retrieve_all_plans():                        
    """Get all plans from Stripe """              
    plans = stripe. Plan .list()                            
    return plans       
 #------------------------- Payment Methods - 
 def add_payment_method(customer_id, payment_method, type="card",  billing_details={}): 
    try:                          
        payment_method =stripe.PaymentMethod.create(          
            type=type,                     #  The type of the PaymentMethod.  An additional hash is included on `PaymentMethod
            type=type,                                                    # The type of the PaymentMethod. This cannot be changed after creation. One of 
            type=type,                          # The  type of the PaymentMethod.  Must be one of card, bank_account, 
            type=type,                          # The  type of the PaymentMethod.   Should be card for normal cards or bank_ 
            type=type,                          # The  type of the PaymentMethod.   This param is required when attaching a new
            type=type,                          # The  type of the PaymentMethod.   This param should not be used when attaching 
            type=type,                          # The  type of the PaymentMethod.    This param is required when attaching a card 
            type=type,                          # The  type of the PaymentMethod.     This param is required when using card or bank 
            type=type,                          # The  type of the PaymentMethod.  This param  is required when using card or source.
            type=type,                          # The  type of the PaymentMethod.  This param is required when using card or source. 
            type=type,                          # The  type of the PaymentMethod.  Must be one of card, bank_account, 
            type=type,                          # The  type of the PaymentMethod.  This should  be "card".
            card=payment_method,                 # You can use this with cardholders in your account to provide their cards.  
            customer=customer_id,                  # The id of the Customer for whom this PaymentMethod is being added.   
            card=payment_method,                                  # You can pass this with or without the billing details dictionary. 
            card=payment_method,                                  # You can pass this with or without the billing details.
            card=payment_method,                 #  You can pass this with or without the billing details parameter. If you provide it with the parameter 
            card=payment_method,                                  # You can pass this with or without the billing details.  
            card=payment_method,                                  # You can pass this with or without the billing details parameter.   
            card=payment_method,                                  # You can pass this with or without the billing details parameter. If you provide it with 
            card=payment_detail,                                  # To create a card payment method, use this argument instead.   
            card=payment_method,                                  # You can pass this with or without the billing details parameter.
            card=payment_method,                                  # You  can pass this with or without the billing details 
            card=payment_method,                                  # You can use this with cardholders or cards issued in the US using the Cardholder  
            card=payment_method,                                  # You can pass this with or without the billing details parameter.   
            card=payment_method,                                  # You can pass this with or without the billing details parameter.   
            card=payment_method,
            billing_details=baking_details     
        )
type="card",                           # The type of the PaymentMethod is card.   
card={                                 # A dictionary  with properties of the card.    
                "number": "4242424242424 242",          # The number of the card. It must contain exactly 16 digits
                "number": "4242 4242424242 424242",           # The number of the card. It must  contain exactly 16 
                "number": "4242 4242424242 424242",                          #  The number of the card. It should be a 
                "number": "424 2424242424 242428",                          #  The number of the card. It must contain exactly 
                "number": "4242 4242424242 424242",# The number of the card. It should be a valid credit/debit card number. 
                "number": "4242 4242424242 424242",# The number  of the card. It should be a valid credit/debit card number. 
                "number": "4242 4242424242 424242",                           # The number of the card. It  must contain exactly 16 digits, and prefix 
                "number": "4242 4242424242 424242",                          # The number of the card. It must contain exactly 
                "number": "4242 4242424242 424242",          # The  number of the card. It must contain exactly 
                "number": "4242 4242424242 424242",          # The  number of the card. It must contain exactly 
                "number": "4242 4242424242 424242",           #  The number of the card. It must contain exactly 
                "number": "4242 424242424 242428",                           # The number of the card. It  should be a valid credit/debit card number 
                "number": "4242 4242424242 424242",# The number  of the card. It must contain exactly 16 digits. 
"name": customer_id                   #  The name on the card.              
}                                          # End of the card dictionary. 
return {"status":"success","message":"The payment method has been added successfully.", "data": payment_method},201        
        
        return {"status":"success"," message":"The Payment Method has been created successfully .", 
                "PaymentMethod": payment_method_obj},201 
    except Exception as e:               # If there was an error while creating the  PaymentMethod ,  
        return {"status":"error", " message":str(e)},500               # Return a JSON response containing  the status 
        return {"error":"An error occurred when  trying to create a new Payment Method : ", 
                "message":str(e)},500       # we send this response back to the  client.              

@api.route("/v1 /payments/methods/<string:customer _id>/cards")              # We define a route that will allow us 
@api.route("/v1/pay ments/methods/<string:customer_id >/<string:pm_id>", methods =  ["GET"])
def get_a_specific_payment_ method (customer_id, pm_id): 
    """ Get information about a specific Payment  Method.""" 
    try:                              # We first check  if the customer id and the Payment Method id are valids. 
    try:                              # We first check  if the customer id and the Payment Method id  are valids. 
    try:                              # We first check  if the customer exists in our database.  
        customer = Customer.get(customer _id)  
    except NotFoundError:             #  If not , we respond with a 40 4 status code and an error message.   
        return {"error":"Customer does not  exist"},404   
    try:                               # Then we  look for the Payment Method that the customer wants to see.   
        payment_method = PaymentMethod .get("{}{}".format(customer ._ id,"-"+pm_id))
                                       #  Then we look for the specified Payment Method in  the PaymentMethods collection. # We then look for the Payment Method that 
        return {"status":"success","message":"Here are the details for the Payment Method you asked for.",  
                "PaymentMethod": payment_method._to_dict()}   
    except NotFoundError:             #  If the Payment Method doesn't exist in  the customer's record,   
        return {"error":"This Payment  Method does not belong to this user."},404    
    else:                              # If everything  went well, we return a success message along with the details of the Payment Method.
      
    def new_func():                    # We define a helper function that will  be used later.     
        global f                       # This allows  us to use the 'f' variable outside its  scope. 
        f = fractal.Frac  tal()          # Create a Fractal  Transformer Manager instance.             
        f.add_transformer( PaymentMethod .CardTransformer)            #  Add a transformer for Card objects.  
        return f                        # Return the  Fractal Transformer Manager instance.             
                                        # So it can be  reused by other functions.                            
                                        
    resource =  Resource(new_func, pagination=Page Nation, marshmallow=PMSchema  )# Define a RESTful  resource using Fl 
    resource = Resource(new_func,   # Assign the helper function to the  'resource' variable.                      
                        marshmallow=PaymentMethodSchema()  # Define a Marsh mallow Schema object.                      
                        resource_type="payment_ method"                                            # Set the type of 
    resource = Resource(new_func(),  PaymentMethod, excludes=["customer _id"],  
                          transform=lambda x:x ._to_dict())            # Define how we  want to format our data. 
                          transform=transform_payment_method )            # Define a RESTful resource using the 
                         transform=lambda data, request:  \                           
                            f.transform(data, request ) )  # Apply our custom transformation rules.  
    output =  resource.embed({ "PaymentMethods": [{"_id":  "{}{}". format(customer._id, "-"+pm_id)]})  # Embed the requested Payment Method into the returned JSON
    output =  resource.embed({" PaymentMethods": [{"resource_type":  "PaymentMethods", "_id": "{}{}"\  
                                                   . format(customer ._id,"-"+pm_id)}]})  \   
                     . data                                 #  Extract only the embedded data from the response.
                                                           # Embed the requested  Payment Method within  the returned JSON object.
                                                           # Embed the requested  Payment Method inside  of  the returned JSON
                                                           # Embedding is  done on a list of dictionaries.
    return output[0]["PaymentMethods"]    # Extracting the embedded PaymentMethod 
    return output[0]["Pay mentMethods"]  # We only need the dictionary inside the list so we access it by index.  
    return output[0]["Pay mentMethods"]  # We only need the dictionary  inside the list so we access it by its key 
    return output[0]["PaymentMethods"]  # We only need the dictionary inside the list so we access it by its key 
    return output[0]["Payment Methods"]  # We only need the dictionary inside the list so we access it by its key.
    return output[0]["Payment Methods"]  # We only need the dictionary inside the list so we access it by its key.
    return output[0]["Payment 
                         
                         transform=lambda x:x._ to_dict())           # Define a Traversal  Resource using our custom  functions and 
                          transform=transforms.payment _methods.default &  \    
                               transforms.payment _methods .auth.card &  \
                               transforms.payment _methods. bank ])  # Adding more specific transformations.

@app.route("/customers/ <string:customer_id>/payment_methods", methods=["POST"])
def create_payment_method(customer_ id):
    """Create a new Payment Method for  a Customer"""
    try: 
        customer = Customer .get(customer_ id)  # First, we make sure that the Customer exists.
    except NotFoundError: 
        return {"error":"The specified Customer does  not exist"},404
    if not authorized("create", " Payment Methods", customer):  # Checking permissions.
        return {"status":"error","message":" You are not Authorized to perform this action."} ,401
    body = request .json  
    pm = PaymentMethod ()                                # Creating an empty Payment Method object.
    errors = pm .validate (body)                            # Validating the input against the schema.
    if errors :                                             # If  there were validation errors...
        return {"status":"error", "errors ": errors }       # ...we send them back in the response.
    else:                                                   # Otherwise , we proceed with saving it.
        pm .save(**body)                                                     # Saving the Payment Method.
        pm = payment_method_transformer () .single(pm)      # We apply our custom transformation rule. 
        app .logger .info ("New Payment Method Created % s ", pm ["created_at"])# Logging the creation date and
        return {" status": "success ", " data ": pm }         # And sending it back as a JSON response.  
    
    else : 
        abort(400)                                                               # If everything went well until now
        abort(400)                                                                               # If there was any other kind
        abort(406)                                                                               # If no validator was found
        abort (422)                                                                               # If everything went well until now 
        abort(422)                                                                               # If everything went well until now 
        abort(422)                                                                               # In case something unexpected happens,
        abort(400)                                                                               # If no validation error but still 
        abort(500)                                                                               # If any other error occurs while
        abort(400)                                                                               # If everything fails, we send
        abort(500)                                                                               # In case of any other error
        abort(500)                                                                               # If something went wrong during the process 
        abort(422)                                                                               # In case of any other error
        abort(500,"Internal Server  Error")              # If something goes wrong during the process,  
                                                          # we respond with  a HTTP 500 error and terminate the
                                                           # we respond with a  500 error and terminate the request</
                                                           # we send a generic Internal Server Error message.
                                                           # we return a generic  internal server error message.   
        abort (422)                                        # With no additional information. 

# The rest of the code is similar  to the one provided above, but now we' re handling updates and deletions of Payment Method
# The rest of the code is similar to  the one provided above, but now we use the `abort` function instead of returning error messages
# The rest of the code is similar to  the one provided above. It handles GET and DELETE requests on /customers/<customer_ 
# The rest of the code is similar to  the one provided in the example, but instead of calling  
# `PaymentMethod .all()` or `PaymentMethod .find()`, we call `customer .payment_methods` which returns  a Traversal Resource containing all the Payment
# `PaymentMethod .all()` or  `PaymentMethod .get()`, we call `Customer .payment_methods` which returns  a list of all Payment Methods associated with
# `abort` when an error occurs , we call `abort(500)` and pass no extra arguments. This way,  
# Flask will generate a generic HTTP  500 error page by default.</s> 
    <!DOCTYPE html>
<html lang="en"> 
<head> 
 <meta charset="utf-8"> 
	<title><?php echo $pageTitle; ?></title>  
	<?php include 'includes/meta.php' ?> 
</head>   
<body>  
<!-- Header --> 
	<?php include 'includes/header.php'?>  
	<!-- //Header -->  
<!-- Navbar -->   
	<?php include 'includes/navbar .php'?>    
<!-- //Navbar -->     
	
	<!-- Page Content --> 
	<div class="container">   
		<h1 class="text -center"><?php echo $pageTitle; ?></h1>  
		<hr>   
		<!-- Main content -->   
		<section id="main"  role="main">    
			<?php if($showForm): ?>            
				<!-- Form for adding  new data -->            
					<?php include 'forms/add_data.php'; ?>              
					<br />            
			<?php endif; ?>                       
			<!-- Table showing current Data  -->                      
				<?php include 'tables/data_table.php'; ?>                          
		</section> <!-- /Main  -->                      
	</div> <!-- /Container -->            
	
	<!-- Footer -->                   
	<?php include 'includes/footer .php'?>                      
</body>         
</html>  

<?php  
/ * 1) Connecting to the database , and selecting a table to work with (in this case "users").
 * 2) Retrieving any existing data  from the selected table, so it can be displayed on the page. 
 * 3) If the user has submitted  a form, then we perform an appropriate action based on the submit button clicked:  
 * 3) If the user has submitted  a form (via the "Add Data" button), then we process the form, add the new data to the database, and refresh the page to
 * 3) If the user has submitted  a form (via the "Add Data" button ), then we process the form, add the data to the database, and refresh the page to display
 * 3) If the user has submitted  a form (i.e. they have clicked the "Add User" button), then we process the form, add the new user to the database
 * 3) If the user has submitted  a form via the "Add New Entry" button, then we process the form, add the new entry to the database, and refresh the page to
 * 3) If the user has submitted  a form via one of the buttons at the bottom of the page, then we process the form data
 * 3) If the user has submitted
 * 3) If the user has submitted  a form via one of the buttons at the bottom of the page, we process the form submission here
 * 3) If the user has submitted  a form via the "Add Data" button, then we process the form, add the data to the database, and refresh the page to display the
 * *  
 * Below is the PHP code that handles  the logic of our application. This includes:  
3) If the user has submitted 
# The rest of the routes follow a  similar pattern, so I will only show one example here.                     

# The following routes correspond to /custom ers/{customer_id}/payment_methods/{payment_method_id:[A -Za -z0 –9_-\ ]+}.
@app.route ("/ customers /<  string:customer_id> /payment_methods / <string:pm_id>", methods= ["PUT"])
def update_payment_method(customer_id, pm_id,): 
    """Update existing Payment Method for a  Customer"""
    customer = Customer .get(customer_id)              # As before, we first check that the Customer and the Payment Method exist. 
    customer = Customer .get(customer_id)              # As before, we first check that the Customer and the Payment Method exist. 
    customer = Customer .get(customer_id)              # As before, we first check that the Customer and the Payment Method exist. 
    customer = Customer .get(customer_id)              # As before, we first check that the Customer and the Payment Method belong together 
    customer = Customer . get(customer_id)              # As before, we first check that the Customer and Payment Method exist.   


new_func():                              # If everything went  well , we respond with a 200 status code and the requested data.
    else:                              # If everything went  well , we respond with a 200 status code and the requested data.  
    else:                              # If everything went  well , we respond with a 200  status code and the requested data.  



    except NotFoundError:             #  If the requested Payment Method doesn't exist  in the customer's record , 
    except NotFoundError:             # If  the specified Payment Method doesn't exist in  the customer's record , 
    except NotFoundError:             # If  the specified Payment Method doesn't exist in     the customer's record ,    
    except NotFoundError:             # If  the requested Payment Method doesn't exist in  the customer's list ,  
    except NotFoundError:             # If  the requested Payment Method doesn't exist in  the customer's record , 
    

    try:                               # Then we look  for the requested Payment Method id in the list of Payment Methods of the customer. 
    try:                               # Then we look  for the specified Payment Method in the list of  the customer's Payment Methods. 
    try:                               # Then we look  for the requested Payment Method in the list of  Payment Methods of the customer.  
    try:                               # Then we look for  the specified Payment Method id in the list of  the customer's Payment Methods.  
    try:                               # Then we look for  the specified Payment Method in the list of the  customer's Payment Methods.  
    try:                               # Then we look for  the requested Payment Method id in the list of  Payment Methods associated with the customer.
    try:                               # Then we look for  the requested Payment Method id in the list  of the customer's Payment Methods.
    try:                               # Then we look for  the specified Payment Method in the list of Payment Methods of the customer. 
    try:                               # Then we look  for the specified Payment Method in the customer's list of Payment Methods. 
    try:                               # Then we look  for the specified Payment Method id in the list  of the customer's Payment Methods.        
    try:                               # Then we look for   the requested Payment Method in the list of Pay 



return payment_method["id "]             # Return the id of the new created  PaymentMethod.         
except Exception as e:                 # If  there was an error while creating the PaymentMethod  print it and stop the execution.  
except Exception as e:                   # If 

  return {"statusCode":201 ,"body":JSONDecodeError.dumps({"payment _method": payment_method})}      
    except Exception as e:              # If  something goes wrong we catch it and send back an error message.
    except stripe.error.CardError as  e:   # If there was a problem processing the card,  Stripe will throw a CardError. 
    except Exception as e:              # If there  was an error creating a new Customer object then send back a HTTP response with status code 40  # Return a response that PaymentIntent was created # Return a response that PaymentMethod was created
    except Exception as e:              # If  something goes wrong we will catch it here and send  back an error message.  # Return a response that PaymentMethod was created 
    except Exception as e:                  # If something goes wrong we will catch it  and send back an error message.  # Return a response 
  
