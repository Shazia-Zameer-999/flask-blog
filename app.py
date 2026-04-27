from flask import Flask, redirect,render_template, request, url_for
import os
from pymongo import MongoClient
from dotenv import load_dotenv
from flask_bootstrap import Bootstrap5
from flask_wtf import FlaskForm,CSRFProtect
from wtforms import StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Email, Length, URL

#loading the configuration from .env file
load_dotenv()

#making the application instance
app=Flask(__name__)
#storing the configuration in variables
app.config['MONGO_URI']=os.getenv("MONGO_URI")
app.config['SECRET_KEY']=os.getenv("SECRET_KEY")

#connecting to the databases- database and collection creation
def get_db():
    client = MongoClient(app.config['MONGO_URI'])
    return client['content']

#printing random secret key for security purposes

Bootstrap5(app)
csrf=CSRFProtect(app)

class CommentForm(FlaskForm):
    username=StringField('Username', validators=[DataRequired(), Length(min=3)],render_kw={"placeholder": "Enter your name"})
    email=StringField('Email', validators=[DataRequired(),Email()])
    website=StringField('Website', validators=[URL(require_tld=True, message='Please enter a valid URL.')], default='')
    comment=TextAreaField('Comment', validators=[DataRequired(), Length(min=10)])
    image_url=StringField('Image URL', validators=[URL(require_tld=True, message='Please enter a valid URL.')], default='')
    submit=SubmitField('Submit')

class ContactForm(FlaskForm):

    name=StringField('Name', validators=[DataRequired(), Length(min=3)],render_kw={"placeholder": "Your Name"})
    email=StringField('Email', validators=[DataRequired(),Email()],render_kw={"placeholder": "Your Email"})
    subject=StringField('Subject', validators=[DataRequired()],render_kw={"placeholder": "Your Subject"})
    message=TextAreaField('Message', validators=[DataRequired(), Length(min=5)],render_kw={"placeholder": "Your Message"})
    submit=SubmitField('Submit')


#routs started here
@app.route('/')
def index():
    db = get_db()
    collection1=db['swiperData']
    if collection1.count_documents({})==0:

            collection1.insert_many([
            {
                "title":"The Best Homemade Masks for Face (keep the Pimples Away)",
                "description":"Lorem ipsum dolor sit amet, consectetur adipisicing elit. Quidem neque est mollitia! Beatae minima assumenda repellat harum vero, officiis ipsam magnam obcaecati cumque maxime inventore repudiandae quidem necessitatibus rem atque.",
                "image_url": url_for('static', filename='img/post-slide-1.jpg')
            },
            {
                "title":"10 Best Nutrition Tips for a Healthy Lifestyle",
                "description":"Lorem ipsum dolor sit amet, consectetur adipisicing elit. Quidem neque est mollitia! Beatae minima assumenda repellat harum vero, officiis ipsam magnam obcaecati cumque maxime inventore repudiandae quidem necessitatibus rem atque.",
                "image_url": url_for('static', filename='img/post-slide-2.jpg')
            },
            {
                "title":"The Ultimate Guide to Homemade Masks for Face",
                "description":"Lorem ipsum dolor sit amet, consectetur adipisicing elit. Quidem neque est mollitia! Beatae minima assumenda repellat harum vero, officiis ipsam magnam obcaecati cumque maxime inventore repudiandae quidem necessitatibus rem atque.",
                "image_url": url_for('static', filename='img/post-slide-3.jpg')
            },
            {
                "title":"5 Easy Ways to Stay Fit and Healthy",
                "description":"Lorem ipsum dolor sit amet, consectetur adipisicing elit. Quidem neque est mollitia! Beatae minima assumenda repellat harum vero, officiis ipsam magnam obcaecati cumque maxime inventore repudiandae quidem necessitatibus rem atque.",
                "image_url": url_for('static', filename='img/post-slide-4.jpg')
            }
            ])

    data=collection1.find()
    
    return render_template('index.html', slides=data)

@app.route('/about')
def about():
    db = get_db()
    collection2=db['teamMembers']
    if collection2.count_documents({})==0:
         collection2.insert_many([
              {
                   "name":"John Doe",
                     "position":"Founder & CEO",
                     "description":"Explicabo voluptatem mollitia et repellat qui dolorum quasi",
                        "image_url": url_for('static', filename='img/team/team-1.jpg')
                   
              },
                {
                     "name":"Jane Smith",
                         "position":"Chief Editor",
                         "description":"Explicabo voluptatem mollitia et repellat qui dolorum quasi",
                            "image_url": url_for('static', filename='img/team/team-2.jpg')
                     
                },
                {
                     "name":"Mike Johnson",
                         "position":"Content Manager",
                         "description":"Explicabo voluptatem mollitia et repellat qui dolorum quasi",
                            "image_url": url_for('static', filename='img/team/team-3.jpg')
                     
                },
                {
                     "name":"Emily Davis",
                         "position":"Marketing Specialist",
                         "description":"Explicabo voluptatem mollitia et repellat qui dolorum quasi",
                            "image_url": url_for('static', filename='img/team/team-4.jpg')
                     
                },
                    {
                        "name":"David Wilson",
                            "position":"Graphic Designer",
                            "description":"Explicabo voluptatem mollitia et repellat qui dolorum quasi",
                                "image_url": url_for('static', filename='img/team/team-5.jpg')
                        
                    },
                    {
                        "name":"Sarah Brown",
                            "position":"Social Media Manager",
                            "description":"Explicabo voluptatem mollitia et repellat qui dolorum quasi",
                                "image_url": url_for('static', filename='img/team/team-6.jpg')
                        
                    }
         ])
    data=collection2.find()
    
    return render_template('about.html', team_members=data)

@app.route('/contact',methods=['GET','POST'])
def contact():

    print(request.method)
    form=ContactForm()
    
    if form.validate_on_submit():
        db=get_db()
        collection=db['contact']
        if collection.find_one({'email':form.email.data}) is None:
            collection.insert_one({
                "name":form.name.data,
                "email":form.email.data,
                "subject":form.subject.data,
                "message":form.message.data
            })
            return redirect(url_for('contact'))
        
    return render_template('contact.html',form=form)

# @app.route('/contact',methods=['GET','POST'])
# @csrf.exempt
# def contact():

#     print(request.method)

#     if request.method=='POST':
#         name=request.form.get('name')
#         email=request.form.get('email')
#         subject=request.form.get('subject')
#         message=request.form.get('message')
#         db=get_db()
#         collection=db['contact']
#         if collection.find_one({'email':email}) is None:
#             collection.insert_one({
#                 "name":name,
#                 "email":email,
#                 "subject":subject,
#                 "message":message
#             })
#             print(request.method)
#             return redirect(url_for('contact'))
#     return render_template('contact.html')

# @app.route('/contact')
# @csrf.exempt
# def contact():
#     return render_template('contact.html')


# @app.post('/contact')
# @csrf.exempt
# def contact_data():
#     name=request.form.get('name')
#     email=request.form.get('email')
#     subject=request.form.get('subject')
#     message=request.form.get('message')
#     db=get_db()
#     collection=db['contact']
#     if collection.find_one({'email':email}) is None:
#         collection.insert_one({
#             "name":name,
#             "email":email,
#             "subject":subject,
#             "message":message
#         })
#         return redirect(url_for('contact'))
#     return render_template('contact.html')



@app.route('/category')
def category():
    return render_template('category.html')

@app.route('/single-post' , methods=['GET','POST'])
def single_post():
    db = get_db()
    collection4=db['comments']
    comments=collection4.find()

    form=CommentForm()
    if form.validate_on_submit():
        # collection4=db['comments']
        if collection4.find_one({'email':form.email.data}) is None:
            collection4.insert_one({
                "username":form.username.data,
                "email":form.email.data,
                "website":form.website.data,
                "comment":form.comment.data,
                "image_url":form.image_url.data
            })
            return redirect(url_for('single_post'))
    count = collection4.count_documents({})

    return render_template('single-post.html', comments=comments,form=form,count=count)

# @app.post('/single-post')
# def single_post_data():
#     # name=request.form.get('username')
#     # email=request.form.get('email')
#     # website=request.form.get('website')
#     # comment=request.form.get('comment')
#     # image_url=request.form.get('img_url')

#     # if image_url=='':
#     #     image_url=url_for('static', filename='img/blog/comments-1.jpg')

#     # errors=[]
#     # if name=='' or email=='' or comment=='':
#     #     errors.append("Please fill in all required fields.")
#     # if '@' not in email:
#     #     errors.append("Please enter a valid email address.")
#     # if len(comment)<10:
#     #     errors.append("Comment must be at least 10 characters long.")
#     # if len(name)<3:
#     #     errors.append("Name must be at least 3 characters long.")    
#     # if len(website)>0 and not website.startswith(('http://', 'https://')):
#     #     errors.append("Please enter a valid website URL (starting with http:// or https://).")

#     # if errors:
#     #     comments=list(db['comments'].find())
#     #     return render_template('single-post.html', errors=errors,comments=comments)
#     # db = get_db()
#     # collection4=db['comments']
#     # if collection4.find_one({'email':email}) is None:
#     #     collection4.insert_one({
#     #         "username":name,
#     #         "email":email,
#     #         "website":website,
#     #         "comment":comment,
#     #         "image_url":image_url
#     #     })


#     # print(name,email,website,comment,image_url)

#     #call the form function which we made as a class
#     form=CommentForm()

#     #if validation is done and there is no error
    

#     db=get_db()
#     if form.validate_on_submit():
#         collection4=db['comments']
#         if collection4.find_one({'email':form.email.data}) is None:
#             collection4.insert_one({
#                 "username":form.username.data,
#                 "email":form.email.data,
#                 "website":form.website.data,
#                 "comment":form.comment.data,
#                 "image_url":form.image_url.data
#             })
#             return redirect(url_for('single_post'))
        
#         #if the validation failed!
#         #again connect to db and fetch the previous comments and render the page with errors and the previous comments
#     comments=list(db['comments'].find())
#     return render_template('single-post.html', form=form, comments=comments)

@app.route('/starter-page')
def starter_page():
    return render_template('starter-page.html')

app.run(debug=True, host="0.0.0.0",port=8000)