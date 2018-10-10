from flask import Flask
from flask import render_template
import jinja2


app = Flask(__name__)

@app.route('/')
def index():
    return 'MI-PYT je nejlepší předmět na FITu!'
    #url = flask.url_for('square', x=5)
    
@app.template_filter('camel')    
def camel_case_filter(txt):
    txt = ''.join(t.title() for t in txt.split('_')) 
    #return jinja2.Markup <i>   

@app.route('/hello')
@app.route('/hello/<name>')
def hello(name=None):
    #return 'MI-PYT je nejlepší předmět na FITu! Hello'
    return render_template('hello.html', username=name)

@app.route('/squared/<int:x>')
def squared(x):
    y = x*x
    return str(y)
