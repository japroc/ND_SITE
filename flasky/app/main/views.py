# -*- coding: utf-8 -*-
from flask import render_template, redirect, url_for, abort, flash, request
from flask_login import login_required, current_user
from . import main
from .forms import EditProfileForm, EditProfileAdminForm, ForMessageForm, SearchForm,f_AddChats, DeleteChats
from .. import db
from ..models import Role, User, Chats, Messages
from ..decorators import admin_required
from flask import jsonify
import requests
from yandex_translate import YandexTranslate
import sys
from datetime import datetime
from sqlalchemy import or_
import calendar
from cachetools import cached, LRUCache




reload(sys)

sys.setdefaultencoding('utf8')





@main.route('/', methods=['GET', 'POST'])
def index():
    reload(sys)
    sys.setdefaultencoding('utf8')
    if current_user.is_authenticated:
        return redirect(url_for('.mess'))
    return render_template('index.html')


@main.route('/send_message', methods=['GET','POST'])
@login_required
def send_message():
    to_id=request.form['id_to']
    data=request.form['message']
    #print("\n\n [***] {0} {1} \n\n".format(to_id,data))
    to_id=to_id.replace("send", "")
    #print ("\n\n {0} \n\n".format(to_id))
    user = User.query.filter_by(username=to_id).first_or_404()
    current_user.add_message(user,data)
    #flash("[*] Your message has been sent.")
    time=datetime.utcnow()
    response=[['time',0],['id_to',0]]
    response_dict = dict(response)
    print response_dict
    response_dict['time']=str(time)
    response_dict['id_to']=user.id
    print response_dict
    return jsonify(response_dict)



@cached(cache=LRUCache(maxsize=1024))
def translate(text,source,dest):
    # print("\n\n {0} {1} {2}".format(text,source,dest))
    translate = YandexTranslate('trnsl.1.1.20190515T114153Z.33301c8ad79f95bd.69a1158dfac270a48213caaf9b6102a3115b8fe1')
    if source =='Eng':
        lang_source='en'
    if source =='Ru':
        lang_source='ru'
    if dest =='Eng':
        lang_dest='en'
    if dest =='Ru':
        lang_dest='ru'
    if source =='Fra':
        lang_source='fr'
    if dest =='Fra':
        lang_dest='fr'

    print(text,source,dest)
    try:
        check = translate.detect(text)
    except:
        print("Check Exception on text: {}".format(text))
        return text
        
    # print("\n\n check: {0}".format(check))
    if not check.find(lang_dest):
        empty = lang_dest + '-' + lang_source
        # print("\n\n empty: {0}".format(empty))
        rez=translate.translate(text, empty)
        s = rez['text'][0].decode('utf8')
        # print(u"\n\n rez: {0}".format(s))
        return s
    return text

@main.route('/update_message', methods=['GET','POST'])
@login_required	
def update_message():
    from_id=request.form['id_2']
    find_new_message=Messages.query.filter_by(to_id=current_user.id,from_id=from_id,check_ms=False).all()
    user = User.query.filter_by(id=from_id).first()
    mess_list = [["count_message", 0], ["messages",[]]]
    if find_new_message==None:
        mess_dict = dict(mess_list)
        return jsonify(mess_dict)
	
    empty=[]
    empty2=[]

    count=0
	
    for mess in find_new_message:
        empty2.append("username")
        empty2.append(user.username)
        empty.append(empty2)
        empty2 = []
        empty2.append("content")
        if (current_user.language != user.language):
            text=translate(mess.content,current_user.language,user.language)
            empty2.append(text)
        else:
            empty2.append(mess.content)
        empty.append(empty2)
        empty2 = []
        empty2.append("id")
        empty2.append(id_1)
        empty.append(empty2)
        empty2=[]
        empty2.append("time")
        empty2.append(mess.created_at)
        empty.append(empty2)
        empty2=[]
        empty2.append("hide")
        empty2.append(mess.content)
        empty.append(empty2)
        empty2=[]
        mess_list[1][1].append(empty)
        empty = []
        count = count + 1
        mess.check_ms=True
        db.session.add(mess)
        db.session.commit()
	
    mess_dict = dict(mess_list)
    for i, l in enumerate(mess_dict['messages']):
        mess_dict['messages'][i] = dict(l)

    mess_dict['count_message']=count
    #print mess_dict

    return jsonify(mess_dict)


@main.route('/get_chats', methods=['GET'])
@login_required
def get_chats():
    def dt_to_ts(dt):
        return calendar.timegm(dt.timetuple())

    all_messages = Messages.query.filter(
        or_(
            Messages.to_id == current_user.id, 
            Messages.from_id == current_user.id, 
        )
    ).all()

    last_per_chat_messages = dict()
    for msg in all_messages:
        chat = "{}_{}".format(min(msg.from_id, msg.to_id), max(msg.from_id, msg.to_id))
        created_at = dt_to_ts(msg.created_at)

        if chat not in last_per_chat_messages:
            last_per_chat_messages[chat] = {
                "message_id": msg.id,
                "to_id": msg.to_id,
                "from_id": msg.from_id,
                "content": msg.content,
                "created_at": created_at,
            }
        else:
            if last_per_chat_messages[chat]["created_at"] < created_at:
                last_per_chat_messages[chat] = {
                    "message_id": msg.id,
                    "to_id": msg.to_id,
                    "from_id": msg.from_id,
                    "content": msg.content,
                    "created_at": created_at,
                }

    users = User.query.all()
    chats = list(last_per_chat_messages.values())
    for chat in chats:
        print("[!] CHATS", current_user.id, chat['from_id'])
        if chat['from_id'] == current_user.id:
            other_user = list(filter(lambda u: u.id == chat['to_id'], users))[0]
            chat['translation'] = chat['content']
            chat['friend_name'] = other_user.username
        else:
            other_user = User.query.filter_by(id=chat['from_id']).first_or_404()
            chat['translation'] = translate(chat['content'], current_user.language, other_user.language)
            chat['friend_name'] = other_user.username
        print("[!] CHATS", chat['content'], chat['translation'])

    return jsonify(chats)


@main.route('/get_messages', methods=['GET'])
@login_required
def get_messages():
    def dt_to_ts(dt):
        return calendar.timegm(dt.timetuple())
    def get_translation(content, from_id, users):
        if from_id == current_user.id:
            return content
        else:
            other_user = list(filter(lambda u: u.id == from_id, users))[0]
            translation = translate(content, current_user.language, other_user.language)
            return translation

    users = User.query.all()

    all_messages = Messages.query.filter(
            or_(
                Messages.to_id == current_user.id, 
                Messages.from_id == current_user.id, 
            )
        ).all()

    messages = list(map(
        lambda msg: {
            "id": msg.id,
            "to_id": msg.to_id,
            "from_id": msg.from_id,
            "content": msg.content,
            "created_at": dt_to_ts(msg.created_at),
            "translation": get_translation(msg.content, msg.from_id, users)
        }
        ,
        all_messages
    ))

    return jsonify(messages)


@main.route('/get_messages_by_id/<int:other_id>', methods=['GET'])
@login_required
def get_messages_by_id(other_id):
    def dt_to_ts(dt):
        return calendar.timegm(dt.timetuple())
    def get_translation(content, from_id, other_user_language):
        if from_id == current_user.id:
            return content
        else:
            translation = translate(content, current_user.language, other_user_language)
            # print(content, other_user_language, current_user.language, translation)
            return translation

    # get other user langugage
    other_user = User.query.filter_by(id=other_id).first_or_404()
    other_user_language = other_user.language

    # messages between you and other any user
    all_messages = Messages.query.filter(
            or_(
                Messages.to_id == current_user.id, 
                Messages.from_id == current_user.id, 
            )
        ).all()

    # messages between you and other specified user
    all_messages = list(filter(
        lambda msg: (msg.to_id == other_id or msg.from_id == other_id)
        , 
        all_messages
    ))

    messages = list(map(
        lambda msg: {
            "id": msg.id,
            "to_id": msg.to_id,
            "from_id": msg.from_id,
            "content": msg.content,
            "created_at": dt_to_ts(msg.created_at),
            "translation": get_translation(msg.content, msg.from_id, other_user_language),
        }
        ,
        all_messages
    ))

    return jsonify(messages)


@main.route('/get_message', methods=['GET','POST'])
@login_required
def get_message():
    from_id=request.form['id_2']
    print("[***] from_id: {0} {1} ".format(from_id,type(from_id)))
    mess_list = [["count_message", 0], ["messages",[]]]

    user = User.query.filter_by(id=from_id).first()
    #print user
    if user==None:
        from_id=from_id.replace("send", "")
        user = User.query.filter_by(username=from_id).first()
        #print("\niasdas here!! {0}\n".format(user))
    all_message = Messages.query.all()
    #for mess in all_message:
    #    mess.delete_mess()

    empty=[]
    empty2=[]

    count=0
    if len(all_message) == 0:
        all_message = None
    else:
        for mess in all_message:
            id_1, id_2 = mess.get_id()
            if id_1 == current_user.id and id_2 == user.id:
                empty2.append("username")
                empty2.append(current_user.username)
                empty.append(empty2)
                empty2=[]
                empty2.append("content")
                empty2.append(mess.content)
                empty.append(empty2)
                empty2=[]
                empty2.append("id")
                empty2.append(id_1)
                empty.append(empty2)
                empty2=[]
                empty2.append("time")
                empty2.append(mess.created_at)
                empty.append(empty2)
                empty2=[]
                empty2.append("hide")
                empty2.append("This is origin language")
                empty.append(empty2)
                empty2=[]
                mess_list[1][1].append(empty)
                empty=[]
                count=count+1
                mess.check_ms=True
                db.session.add(mess)
                db.session.commit()

            if id_2 == current_user.id and id_1== user.id:
                empty2.append("username")
                empty2.append(user.username)
                empty.append(empty2)
                empty2 = []
                empty2.append("content")
                if (current_user.language != user.language):
                    text=translate(mess.content,current_user.language,user.language)
                    empty2.append(text)
                else:
                    empty2.append(mess.content)
                empty.append(empty2)
                empty2 = []
                empty2.append("id")
                empty2.append(id_1)
                empty.append(empty2)
                empty2=[]
                empty2.append("time")
                empty2.append(mess.created_at)
                empty.append(empty2)
                empty2=[]
                empty2.append("hide")
                empty2.append(mess.content)
                empty.append(empty2)
                empty2=[]
                mess_list[1][1].append(empty)
                empty = []
                count = count + 1
                mess.check_ms=True
                db.session.add(mess)
                db.session.commit()


    mess_dict = dict(mess_list)
    for i, l in enumerate(mess_dict['messages']):
        mess_dict['messages'][i] = dict(l)

    mess_dict['count_message']=count
    #print mess_dict

    return jsonify(mess_dict)



@main.route('/mess',methods=['GET','POST'])
@login_required
def mess():
    form=SearchForm()
    if form.validate_on_submit():
        #When user click SEARCH!
        return redirect((url_for('.search_results', query=form.search.data)))

    all_chats=Chats.query.all()
    real_chats=[]
    #real_chats = [[0] * 2 for i in range(len(all_chats))]
    if len(all_chats)==0:
        real_chats=None
    else:
        for chat in all_chats:
            id_1,id_2=chat.get_id()
            #print("\n\n {0} {1} {2} {3}\n\n".format(id_1,id_2,type(id_1),type(chat)))
            if id_1 == current_user.id :
                real_chats.append(id_2)
            if id_2 == current_user.id:
                real_chats.append(id_1)

    real_rez=[]
    results = User.query.all()
    if len(results) == 0:
        real_rez = None


    for rez in results:
        for rez2 in real_chats:
            if rez2  == rez.id:
                real_rez.append(rez)


    #for_mess=ForMessageForm()
    #if for_mess.validate_on_submit():

    #print ("\n\n [***] {0} \n\n ".format(real_chats))
    form_for_message=ForMessageForm()
    if form_for_message.validate_on_submit():
        message=form_for_message.message.data

    return render_template('main.html',form=form, result=real_chats, name_chats=real_rez, form_mess=form_for_message)

# @main.route('api/search/<query>',methods=['GET','POST'])
# @login_required
# def search_results(query):

@main.route('/search_result/<query>',methods=['GET','POST'])
@login_required
def search_results(query):
  form = SearchForm()
  if form.validate_on_submit():
      # When user click SEARCH!
      #print("[***] {0} ".format(form.search.data))
      return redirect((url_for('.search_results', query=form.search.data)))
  results = User.query.all()
  #print type(results)
  real_result=[]
  if len(results)==0:
      real_result = None
  else:
      for rez in results:
          #print("\n\n[*] {0} {1}\n\n".format(rez.get_name(),type(rez)))
          real_result.append(rez.get_name())
  real_rez=[]
  #print query
  for rez in real_result:
      if rez.find(query) != -1:
          real_rez.append(rez)
  return render_template('main.html',form=form, query=query, results=real_rez)

  
@main.route('/delete_chat/<index>', methods=['POST'])
@login_required
def doit(index):
    #print index
	user = User.query.filter_by(id=index).first()
	find_chats=Chats.query.filter_by(fr_one_id=current_user.id,fr_two_id=user.id).first()
        if find_chats != None:
            find_chats.delete_chat()
        else:
            find_chats=Chats.query.filter_by(fr_one_id=user.id,fr_two_id=current_user.id).first()
            if find_chats != None:
                find_chats.delete_chat()
        
        flash('Chat with %s delete.' % user.username)
        return redirect(url_for('.mess'))


@main.route('/user/<username>', methods = ['GET', 'POST'])
def user(username):
    adds=f_AddChats()
    if adds.validate_on_submit():
        user = User.query.filter_by(username=username).first()
        if user is None:
            flash('Invalid user.')
            return redirect(url_for('.index'))
        if current_user.check_chats(user) == True:
            flash('You are already chats this user.')
            return redirect(url_for('.user', username=username))

        if current_user.check_chats2(user) == True:
            flash('You are already chats this user.')
            return redirect(url_for('.user', username=username))

        current_user.add_chats(user)
        flash('Chat with %s added!.' % username)
        return redirect(url_for('.mess'))
	
	
    user = User.query.filter_by(username=username).first_or_404()
	
#    deletes=DeleteChats()
#    if deletes.validate_on_submit():
#        find_chats=Chats.query.filter_by(fr_one_id=current_user.id,fr_two_id=user.id).first()
#        if find_chats != None:
#            find_chats.delete_chat()
#        else:
#            find_chats=Chats.query.filter_by(fr_one_id=user.id,fr_two_id=current_user.id).first()
#            if find_chats != None:
#                find_chats.delete_chat()
#        
#        flash('Chat with %s delete.' % username)
#        return redirect(url_for('.mess'))
    all_chats=Chats.query.all()
    real_chats=[]
    #real_chats = [[0] * 2 for i in range(len(all_chats))]
    if len(all_chats)==0:
        real_chats=None
    else:
        for chat in all_chats:
            id_1,id_2=chat.get_id()
            #print("\n\n {0} {1} {2} {3}\n\n".format(id_1,id_2,type(id_1),type(chat)))
            if id_1 == current_user.id :
                real_chats.append(id_2)
            if id_2 == current_user.id:
                real_chats.append(id_1)

    

    chats_is=False
    for rez2 in real_chats:
        if rez2  == user.id:
            chats_is=True
	
	
    return render_template('user.html', user=user, adds=adds,chats_iss=chats_is)


@main.route('/edit-profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm()
    if form.validate_on_submit():
        current_user.name = form.name.data
        current_user.location = form.location.data
        current_user.about_me = form.about_me.data
        db.session.add(current_user._get_current_object())
        db.session.commit()
        flash('Your profile has been updated.')
        return redirect(url_for('.user', username=current_user.username))
    form.name.data = current_user.name
    form.location.data = current_user.location
    form.about_me.data = current_user.about_me
    return render_template('edit_profile.html', form=form)


@main.route('/edit-profile/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_profile_admin(id):
    user = User.query.get_or_404(id)
    form = EditProfileAdminForm(user=user)
    if form.validate_on_submit():
        user.email = form.email.data
        user.username = form.username.data
        user.confirmed = form.confirmed.data
        user.role = Role.query.get(form.role.data)
        user.name = form.name.data
        user.location = form.location.data
        user.about_me = form.about_me.data
        db.session.add(user)
        db.session.commit()
        flash('The profile has been updated.')
        return redirect(url_for('.user', username=user.username))
    form.email.data = user.email
    form.username.data = user.username
    form.confirmed.data = user.confirmed
    form.role.data = user.role_id
    form.name.data = user.name
    form.location.data = user.location
    form.about_me.data = user.about_me
    return render_template('edit_profile.html', form=form, user=user)

@main.route('/me', methods=['GET'])
@login_required
def me():
    user = User.query.filter_by(id=current_user.id).first_or_404()
    res = {
        'id': user.id,
        'email': user.email,
        'username': user.username,
        'language': user.language,
    }
    print(res)
    return jsonify(res)
