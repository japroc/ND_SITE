import os
from flask_migrate import Migrate, upgrade
from app import create_app, db
from app.models import User, Role, Chats,Permission,Messages

from flask import request
from flask import jsonify
from flask_socketio import SocketIO, emit
from flask_login import login_required, current_user
from datetime import datetime
from yandex_translate import YandexTranslate
import calendar
from sqlalchemy import or_

async_mode = None



app = create_app(os.getenv('FLASK_CONFIG') or 'default')
migrate = Migrate(app, db)



def translate(text,source,dest):
    # print("\n\n {0} {1} {2} \n\n".format(text,source,dest))
    translate = YandexTranslate('trnsl.1.1.20190515T114153Z.33301c8ad79f95bd.69a1158dfac270a48213caaf9b6102a3115b8fe1')
    if source =='Eng':
        lang_source='en'
    if source =='Ru':
        lang_source='ru'
    if dest =='Eng':
        lang_dest='en'
    if dest =='Ru':
        lang_dest='ru'
    if source == 'Fra':
        lang_source='fr'
    if dest =='Fra':
        lang_dest='fr'

    try:
        check = translate.detect(text)
    except:
        print("Check Exception on text: {}".format(text))
        return text

    # print("\n\n check: {0} \n\n".format(check))
    if not check.find(lang_dest):
        empty = lang_dest + '-' + lang_source
        #print("\n\n empty: {0} \n\n".format(empty))
        rez=translate.translate(text, empty)
        s = rez['text'][0].decode('utf8')
        # print(u"\n\n rez: {0} \n\n".format(s))
        return s
    return text

@app.shell_context_processor
def make_shell_context():
    return dict(db=db, User=User, Role=Role, Chats=Chats, Permission=Permission,Messages=Messages)



socketio = SocketIO(app, async_mode=async_mode)

clients = []

@socketio.on('want_connect', namespace='/test')
def connect_client(msg):
    # print ("\n[***] We connect: {0}  by {1}\n".format(current_user.username, request.sid))
    connecter={"sid" : request.sid, "id": current_user.id}
    clients.append(connecter)
    print(clients)
    emit('connected', {'data': 'yeap'})



@socketio.on('disconnect', namespace='/test')
def disconnect_client():
    #print('Client disconnected')
    # print ("\n[***] We disconnect: {0}  by {1}\n".format(current_user.username, request.sid))
    # print clients
    for client in clients:
        if client["sid"] == request.sid:
            clients.remove(client)

    # print clients

@socketio.on('send_message', namespace='/test')
def send_message(msg):
    def dt_to_ts(dt):
        return calendar.timegm(dt.timetuple())
    #print ("\n[***]client {0} send: {1} to {2} \n".format(current_user.username,msg['content'],msg['to_id']))
    content=msg['content']

    print("[!] send_message", msg)
    try:
        to_id=int(msg['to_id'])
        user = User.query.filter_by(id=to_id).first_or_404()
    except:
        to_id=msg['to_id'].replace("send", "")
        user = User.query.filter_by(username=to_id).first_or_404()

    # create new chat if new
    chats = Chats.query.filter(
        or_(
            Chats.fr_one_id == current_user.id,
            Chats.fr_otwo_id == current_user.id,
        )
    ).all()
    chat = list(filter(
        lambda chat: chat.fr_one_id == user.id or chat.fr_two_id == user.id
        , 
        chats
    ))
    if not chat:
        current_user.add_chats(user)
        # new_chat = Chat(fr_one_id=current_user.id, fr_two_id=user.id)
        # Chats.add(new_chat)

    #print("[*] to_id:{0}".format(to_id))
    current_user.add_message(user, content)
    time = datetime.utcnow()
    #mess=[['content',content],['time',time],['hide','This is origin language'],['id',user.id]]
    #mess_dict=dict(mess)

    response = [['content', 0], ['time', 0],['hide',0],['id',0],['username',0]]
    response_dict = dict(response)
    response_dict['time'] = str(time)
    response_dict['created_at'] = dt_to_ts(time)
    response_dict['content'] = content
    response_dict['hide'] = 'This is origin language'
    response_dict['translation'] = 'This is origin language'
    response_dict['id'] = user.id
    response_dict['username'] = current_user.username
    for client in clients:
        if client["id"] == current_user.id:
            for_room_one=client["sid"]
            emit('print_my_send',response_dict,room=for_room_one)

    if (current_user.language != user.language):
        text = translate(content, user.language,current_user.language)
        # print ("YEAP!")
        # print text
    else:
        # print("asdasdasdsa")
        text=content
        content='This is origin language'

    #mess2 = [['content', text], ['time', time], ['hide', content], ['id', current_user.id]]
    #mess2_dict=dict(mess2)
    # print text
    response2 = [['content', 0], ['time', 0], ['hide', 0], ['id', 0],['username',0]]
    response_dict2 = dict(response2)
    response_dict2['time'] = str(time)
    response_dict2['created_at'] = dt_to_ts(time)
    response_dict2['content'] = text
    response_dict2['mobile_content'] = content
    response_dict2['hide'] = content
    response_dict2['translation'] = text
    response_dict2['id'] = current_user.id
    response_dict2['username']=current_user.username
    response_dict2['friend_id']=user.id
    response_dict2['friend_username']=user.username

    for_room=0
    for client in clients:
        if client["id"] == user.id:
            for_room=client["sid"]
            emit('print_to_me', response_dict2,room=for_room)



#@app.cli.command()
#def test():
#    """Run the unit tests."""
#    import unittest
#    tests = unittest.TestLoader().discover('tests')
#    unittest.TextTestRunner(verbosity=2).run(tests)

if __name__ == "__main__":
    #upgrade()
    #app.run(host="0.0.0.0",processes=3)
    socketio.run(app, debug=True,host="0.0.0.0")