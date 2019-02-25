import json
import requests
import time
from dbhelper import DBHelper
from urllib.parse import quote_plus
from os import listdir, environ
import emoji
from models import obesity_risk
import csv
from utils import md5
from g0d_m0d3 import h4ck
import argparse
from pandas import read_csv
from threading import Thread
from math import ceil
import datetime

# global variables to use
# througth different functions
global URL
global debug
global languages
global images
global def_lang_
global negations
global affirmations
global roles
global db
global nq_category
global rules
global god_mode
global statistics_word
global init_date


###############
#
#   ERROR LOG
#
################
def log_entry(entry):
    # get actual time
    now = datetime.datetime.now()
    dateerror = now.strftime("%Y-%m-%d %H:%M")
    # open the log file in append mode
    with open('error.log', 'a') as log:
        log.write('\n' + dateerror + '\n')
        log.write(str(entry) + '\n\n')


#################
#
#   BASIC TOOLS
#
################

def build_keyboard(items):
    # contruir un teclado para una vez
    keyboard = [[item] for item in items]
    reply_markup = {"keyboard": keyboard, "one_time_keyboard": True}
    return json.dumps(reply_markup)


# funcion auxiliar de nivel mas bajo para recibir mensajes
def get_url(url):
    # funcion para recibir lo que se le pasa al bot
    response = requests.get(url)
    content = response.content.decode("utf8")
    return content


def get_json_from_url(url):
    # obteniene lo que se le pasa al bot con la funcion auxiliar
    content = get_url(url)
    # transforma de JSON a diccionario
    js = json.loads(content)
    return js


def get_updates(offset=None):
    # peticion para obtener las novedades
    url = URL + "getUpdates"
    # offset es el numero del ultimo mensaje recibido
    # el objetivo es no volver a pedirlo to-do
    if offset:
        url += "?offset={}".format(offset)
    # llamada a la funcion auxiliar
    js = get_json_from_url(url)
    return js


def get_last_update_id(updates):
    # el orden de llegada de los mensajes al bot produce un id creciente
    # devolvemos el maximo para saber por donde nos hemos quedado
    update_ids = []
    return max([int(el['update_id']) for el in updates['result']])


#################
#
#   TELEGRAM API MACROS
#
#################

def getMe():
    # Check API method
    getme = URL + "getMe"
    print(get_url(getme))


def send_message(text, chat_id, reply_markup=None):
    text = quote_plus(text)
    url = URL + "sendMessage?text={}&chat_id={}&parse_mode=Markdown".format(text, chat_id)
    # reply_markup is for a special keyboard
    if reply_markup:
        url += "&reply_markup={}".format(reply_markup)
    return get_url(url)


def send_image(img, chat_id, caption=None):
    # give the name of a file in 'img' folder
    # send that image to the user
    url = URL + "sendPhoto"
    files = {'photo': img}
    data = {'chat_id': chat_id}
    if caption:
        data['caption'] = caption
    requests.post(url, files=files, data=data)


def send_sticker(sticker_id, chat_id):
    # send an sticker
    url = URL + "sendSticker"
    # atributtes
    data = {'chat_id': chat_id, 'sticker': sticker_id}
    # it returns the same file if success, can be stored in a variable
    requests.post(url, data=data)


def forward(chat_from, msg_id, chat_id):
    # forward a messege
    url = URL + "forwardMessage"
    # atributtes
    data = {'chat_id': chat_id, 'from_chat_id': chat_from, 'message_id': msg_id}
    requests.post(url, data=data)


def send_GIF(localpath, chat_id):
    # sent a short video as a GIF
    url = URL + "sendVideo"
    # atributtes
    files = {'video': open('img/' + localpath, 'rb')}
    data = {'chat_id': chat_id}
    requests.post(url, files=files, data=data)


def send_file(localpath, chat_id):
    # sent a short video as a GIF
    url = URL + "sendDocument"
    # atributtes
    files = {'document': open(localpath, 'rb')}
    data = {'chat_id': chat_id}
    print(requests.post(url, files=files, data=data))


###############################
#
#   BOT SPECIFIC METHODS
#
###############################
def load_rules():
    '''
    Loads the especific range rules for each question
    returns dict
    '''
    rules = {}
    df_ = read_csv('ranges.csv', sep=',')
    for _, row in df_.iterrows():
        question = (row['phase'], row['question'])
        aux_ = {'type': row['type'], 'low': row['low'], 'high': row['high']}
        rules[question] = aux_
    return rules


def checkanswer(str, status):
    '''
    Determine if an answer is valid
    '''
    # maximum string length accepted
    if len(str) > 20:
        return None, False

    try:
        ranges = rules[status]
        # numeric values
        if ranges['type'] == 'int' or ranges['type'] == 'float':
            val = float(str.replace(',', '.'))
            assert ranges['low'] <= val <= ranges['high']
            return val, True

        # yes/no questions
        elif ranges['type'] == 'affirmation':
            if str.lower() in affirmations:
                return 1, True
            elif str.lower() in negations:
                return 0, True
            else:
                return None, False

        # no text restrictions
        elif ranges['type'] == 'text':
            return str, True

    except:
        return None, False


##############################
#
#   MAIN FUNCTIONS
#
#############################


def process_lang(language):
    '''
    By the moment this method only allows
    one language. TODO -> Implement multilanguage as files become ready
    '''
    return def_lang_


def load_images():
    # since there is only few pictures
    # load the in advance
    images_ = {}
    for lang in listdir('img'):
        dict_ = {}
        if lang.startswith('.'):
            continue
        for f in listdir('img/' + lang):
            with open('img/' + lang + '/' + f, 'rb') as img:
                dict_[f] = img.read()
        images_[lang] = dict_
    return images_


def load_languages():
    langs_ = {}
    for f in listdir('strings'):
        dict_ = {}
        try:
            with open('strings/' + f, 'r', encoding='utf-8') as csvfile:
                # may happen this is not a csv file
                if not f.endswith('.csv'):
                    continue
                csv_ = csv.reader(csvfile, delimiter=',')
                for row in csv_:
                    dict_[row[0]] = row[1]
            langs_[f.split('.')[0]] = dict_
        except Exception as e:
            log_entry(e)
            continue  # sanity check
    return langs_


def get_chat(update):
    if 'edited_message' in update and 'text' in update['edited_message']:
        return update['edited_message']['chat']['id']

    elif 'callback_query' in update:
        return update['callback_query']['from']['id']

    else:
        return update["message"]["chat"]["id"]


def filter_update(update):
    if 'edited_message' in update:
        if 'text' in update['edited_message']:
            process_edit(update)
            return False, update['edited_message']['message_id']
        else:
            # returning none if it's an update without text -> i.e and image
            return None, None

    elif 'callback_query' in update:
        # data is the text sent by the callback as a msg
        return update['callback_query']['data'], update['callback_query']['message']['message_id']

    elif 'message' in update:
        if 'text' in update['message']:
            return update["message"]["text"].strip(), update['message']['message_id']

        else:
            # return none if it's a message withpout text
            return None, update['message']['message_id']

    else:  # inline query for example
        return False, None


def process_edit(update):
    text = update["edited_message"]["text"]
    message_id = update['edited_message']['message_id']
    # get the status of that message_id
    status = db.get_status_by_id_message(message_id)
    try:
        text, flag = checkanswer(text, status)
        if flag:
            db.update_response_edited(message_id, text)
    except Exception as e:
        log_entry('Captured error at editing message.')


def go_main(chat, lang):
    '''
    Macro for setting up one user to the main phase
    '''
    db.change_phase(newphase=0, id_user=md5(chat))
    send_message(languages[lang]['select'], chat, main_menu_keyboard(chat, lang))


def dynamic_keyboard(string, lang='en'):
    '''
    This is a keyboard created for selecting the type of person to share
    '''
    options = [el for el in languages[lang][string].split('\n') if el]
    key_ = []
    aux_ = []
    for i in range(len(options)):
        callback_ = options[i]
        if ':' in callback_:
            # TODO IMPROVE THIS -> maybe regex
            # Just remove from the first : to the end
            callback_ = callback_[:callback_.index(':')]
        aux_.append({'text': emoji.emojize(options[i]), 'callback_data': options.index(callback_)})
        if i % 2 == 1:
            key_.append(aux_)
            aux_ = []
    print(key_)
    keyboard = {'inline_keyboard': key_}
    return json.dumps(keyboard)


def main_menu_keyboard(chat, lang='en'):
    options = [el for el in languages[lang]['options'].split('\n') if el]
    personal = options[0]
    food = options[1]
    activity = options[2]
    completed = db.check_completed(md5(chat))

    if completed[0]:
        personal += '\t\t:white_heavy_check_mark:'
    if completed[1]:
        food += '\t\t:white_heavy_check_mark:'
    if completed[2]:
        activity += '\t\t:white_heavy_check_mark:'

    keyboard = {'inline_keyboard': [[{'text': emoji.emojize(personal), 'callback_data': 'personal'},
                                     {'text': emoji.emojize(food), 'callback_data': 'food'}],
                                    [{'text': emoji.emojize(activity), 'callback_data': 'activity'},
                                     {'text': emoji.emojize(options[3]), 'callback_data': 'risk'}],
                                    [{'text': emoji.emojize(options[5]), 'callback_data': 'share'},
                                     {'text': emoji.emojize(options[6]), 'callback_data': 'credits'}]]}
    return json.dumps(keyboard)


def detailed_wakamola_keyboard(lang='en'):
    '''
    A simple button for getting a detailed wakamola explanation
    '''
    global languages
    keyboard = {'inline_keyboard': [[{'text': languages[lang]['get_details'], 'callback_data': 'risk_full'}]]}
    return json.dumps(keyboard)


def questionarie(num, chat, lang, msg=None):
    '''
    Method to start a questionnatie flow
    TODO This can be parametrized and be way more general
    '''
    db.change_phase(newphase=num, id_user=md5(chat))
    if num == 1:
        send_image(images[lang]['personal.jpg'], chat)
    elif num == 2:
        send_image(images[lang]['food.jpg'], chat)
    elif num == 3:
        send_image(images[lang]['activity.jpg'], chat)

    if msg:
        send_message(msg, chat)
    # edit instruction
    send_message(languages[lang]['edit'], chat)
    # throw first question
    q1 = db.get_question(phase=num, question=1, lang=lang)
    # error on the database
    if q1 is None:
        return
    # check for "extra" (out of the normal q-a flow) messages
    extra_messages(num, 1, chat, lang)
    send_message(emoji.emojize(q1), chat)


def create_shared_link(chat, social_role):
    token = db.create_short_link(id_user=md5(chat), type=social_role)
    return 't.me/{}?start={}'.format(BOT_USERNAME, token)


def extra_messages(phase, question, chat, lang):
    '''
    This method includes all the extra messages that break the
    usual question - response - question... flow
    TODO parametrize this in order to be less horrendous
    '''
    # food
    if phase == 2 and question == 10:  # weekly questionnarie
        send_message(languages[lang]['food_weekly'], chat)


def avocados(score):
    '''
    This function returns a String
    containing N avocado emojis
    '''
    avo_emojis_ = " :avocado: :avocado: :avocado:"
    for its in range(int(score / 20)):
        avo_emojis_ += " :avocado:"
    return avo_emojis_


def weight_category(bmi, lang):
    categories = languages[lang]['pesos'].split('\n')
    if bmi < 18.5:
        weight_cat = categories[0]
    elif bmi < 25:
        weight_cat = categories[1]
    elif bmi < 30:
        weight_cat = categories[2]
    elif bmi < 35:
        weight_cat = categories[3]
    else:
        weight_cat = categories[4]
    return weight_cat


def n_avocados(value, minimum=0, maximum=10):
    base = ':avocado:'
    res = ''
    # change base from 0 to max, then set a minimum value
    # 100 is the max value in all the metrics
    n = max(ceil(value * maximum / 100), minimum)
    for _ in range(n):
        res += base
    return res

def wakaestado(chat, lang):
    '''
    Piece of the standard flow to calculate and send the wakaestado
    '''

    completed = db.check_completed(md5(chat))
    # put phase to 0
    db.change_phase(newphase=0, id_user=md5(chat))

    # final risk and "explanation"
    risk, partial_scores = obesity_risk(md5(chat), completed)
    risk = round(risk)

    # imagen wakaestado
    send_image(images[lang]['wakaestado.jpg'], chat)

    # wakaestado detailed
    if completed[0] and completed[1] and completed[2]:
        # nutrition, activity, bmi, risk, network
        # normal weight, overweight...
        weight_cat = weight_category(round(partial_scores['bmi']), lang)

        difference = partial_scores['mean_contacts'] - partial_scores['wakascore']
        # load "debajo/arriba" string
        index = 0 if difference > 0 else 1
        position = languages[lang]['posicion_media'].split('\n')[index]
        details = languages[lang]['wakaestado_detail']
        details = details.format(str(risk) + n_avocados(risk),
                                 str(abs(round(difference))),
                                 position,
                                 str(partial_scores['n_contacts']),
                                 str(round(partial_scores['nutrition'])) + n_avocados(partial_scores['nutrition']),
                                 str(round(partial_scores['activity'])) + n_avocados(partial_scores['activity']),
                                 str(round(partial_scores['bmi_score'])) + n_avocados(partial_scores['bmi_score']),
                                 str(round(partial_scores['bmi'])),
                                 weight_cat,
                                 str(round(partial_scores['network'])) + n_avocados(partial_scores['network']))

        send_message(emoji.emojize(details), chat)

    # WakaEstado partial
    else:
        # give a general advice
        send_message(emoji.emojize(languages[lang]['wakaestado_parcial'].format(str(risk) + avocados(risk))), chat)


def handle_updates(updates):
    for update in updates:
        chat = get_chat(update)
        text, message_id = filter_update(update)

        if debug:
            print(chat, text)

        # no valid text
        if text is False:
            return

        elif text is None:
            lang = process_lang(update['message']['from']['language_code'])
            send_message(languages[lang]['not_supported'], chat)
            return
        # get user language
        lang = def_lang_
        if 'message' in update:
            if 'language_code' in update['message']['from']:
                lang = process_lang(update['message']['from']['language_code'])
            else:
                lang = def_lang_
        # callback version of the language
        elif 'callback_query' in update:
            if 'language_code' in update['callback_query']['from']:
                lang = process_lang(update['callback_query']['from']['language_code'])

        # start command / second condition it's for the shared link
        if text.lower() == 'start' or '/start' in text.lower():
            # wellcome message
            send_image(images[lang]['welcome.jpg'], chat)
            send_message(emoji.emojize(languages[lang]['welcome']), chat, main_menu_keyboard(chat, lang))
            # insert user into the db, check collisions
            if not db.check_start(md5(chat)):
                # sanity check
                try:
                    db.register_user(id_user=md5(chat), language=lang)
                except Exception as e:
                    log_entry("Error registering the user")
            else:
                db.change_phase(newphase=0, id_user=md5(chat))

            # check for the token
            if ' ' in text:
                aux = text.split(' ')
                # TOKEN CHECK -> AFTER REGISTRATION
                if len(aux) == 2:
                    # token base64 is in the second position
                    friend_token, role = db.get_short_link(aux[1])
                    try:
                        # friend token already in md5 -> after next code block
                        db.add_relationship(md5(chat), friend_token, role)
                    except Exception as e:
                        print('Error ocurred on relationship add', e)
                        log_entry(e)

        # Check if the user have done the start command
        elif db.check_user(md5(chat)):
            # if not, just register him and made him select
            db.register_user(id_user=md5(chat), language=lang)
            db.change_phase(newphase=0, id_user=md5(chat))
            send_message(languages[lang]['select'], chat)

        elif text.lower() == 'credits':
            # just sed a message with the credits and return to the main menu
            send_message(languages[lang]['credits'], chat)
            # send_file('theme definitivo.tdesktop-theme', chat)
            go_main(chat, lang)

        elif text.lower() == 'share':
            send_image(images[lang]['wakanetwork.jpg'], chat)
            # get the number of contacts in each category
            contacts_counter = db.get_contacts_by_category(md5(chat))
            msg_share = languages[lang]['share'].format(
                str(sum(contacts_counter.values())),
                str(contacts_counter['home']),
                str(contacts_counter['family']),
                str(contacts_counter['friend']),
                str(contacts_counter['coworker'])
            )
            send_message(emoji.emojize(msg_share), chat)
            send_image(images[lang]['help.jpg'], chat)
            # get the different links for sharing
            # OJO estan en el orden adecuado ahora
            links = [create_shared_link(chat, r).replace('_', '\\_') for r in roles]
            for i in range(len(links)):
                # first of the four messages is the share2
                send_message(emoji.emojize(languages[lang]['share'+str(i+2)].format(links[i])), chat)
            go_main(chat, lang)
            return

        elif text.lower() == 'personal':
            # set to phase and question 1
            questionarie(1, chat, lang)
            return

        elif text.lower() == 'food':
            # set to phase and question 2
            questionarie(2, chat, lang, msg=languages[lang]['food_intro'])
            return

        elif text.lower() == 'activity':
            # set to phase and question 3
            questionarie(3, chat, lang)
            return

        elif text.lower() == 'risk':
            wakaestado(chat=chat, lang=lang)
            go_main(chat=chat, lang=lang)
            return

        elif text.lower() == god_mode:
            h4ck(md5(chat))
            go_main(chat=chat, lang=lang)

        # hardcoded statistics
        elif text.lower() == statistics_word:
            dbnumbers = db.statistics()
            date_now = datetime.datetime.now()
            time_diff = date_now - init_date
            days_ = time_diff.days
            seconds_ = time_diff.seconds
            minutes_ = seconds_ // 60
            seconds_ = seconds_ % 60
            hours_ = minutes_ // 60
            minutes_ = minutes_ % 60
            txt_ = "Completado todo: {}\nIniciado el bot: {}\nNumero de relaciones: {}\nUptime: {}".format(
                str(dbnumbers[0]),
                str(dbnumbers[1]),
                str(dbnumbers[2]),
                "Days: {} Hours: {} Minutes: {} Seconds: {}".format(days_, hours_, minutes_, seconds_)
            )
            send_message(txt_, chat)
            go_main(chat=chat, lang=lang)

        else:
            # rescata a que responde
            status = db.get_phase_question(md5(chat))
            if status[0] == 0:
                send_message(languages[lang]['select'], chat, main_menu_keyboard(chat, lang))
                return

            text, correct_ = checkanswer(text, status)
            if correct_:
                # store the user response
                db.add_answer(id_user=md5(chat), phase=status[0], question=status[1], message_id=message_id,
                              answer=text)

            else:
                send_message(languages[lang]['numeric_response'], chat)
                # repeat last question
                q = db.get_question(status[0], status[1], lang)
                # error on the database
                if q is None:
                    return
                send_message(emoji.emojize(q), chat)
                return

            # check for more questions in the same phase
            if nq_category[status[0]] > status[1]:
                # advance status
                db.next_question(md5(chat))
                # special cases
                skip_one_ = False
                # if the users answers 0 in certain question
                # we have to omit the folowing questions
                if (status[0] == 3 and status[1] == 1) or (status[0] == 3 and status[1] == 3) or \
                        (status[0] == 3 and status[1] == 5):
                    if int(text) < 1:
                        skip_one_ = True

                if skip_one_:
                    # save 0 in the next question
                    db.add_answer(id_user=md5(chat), phase=status[0], question=status[1] + 1,
                                  message_id=message_id * -1,
                                  answer=0)
                    # forward the status again
                    db.next_question(md5(chat))
                    # get the corresponding question
                    q = db.get_question(status[0], status[1] + 2, lang)
                else:
                    # pick up next question
                    q = db.get_question(status[0], status[1] + 1, lang)
                    # error on the database
                if q is None:
                    return
                # comprueba si tiene que lanzar algun mensaje antes de la pregunta
                extra_messages(status[0], status[1] + 1, chat, lang)
                # TODO OPCIONES DE RESPUESTA DINAMICAS
                if status[0] == 1 and status[1] == 8:  # genero

                    print(send_message(emoji.emojize(q), chat, dynamic_keyboard('generos', lang)))

                elif status[0] == 1 and status[1] == 10:  # nivel estudios
                    print(send_message(emoji.emojize(q), chat, dynamic_keyboard('estudios', lang)))

                elif status[0] == 1 and status[1] == 11:  # estado civil
                    print(send_message(emoji.emojize(q), chat, dynamic_keyboard('estado_civil', lang)))

                else:
                    send_message(emoji.emojize(q), chat)
            else:
                # si lo es, actualiza estatus y "vuelve" al menu principal
                db.completed_survey(md5(chat), status[0])
                db.change_phase(newphase=0, id_user=md5(chat))

                # NEW V2, depending on the questionnarie displat a diferent message
                if status[0] == 1:
                    send_message(emoji.emojize(languages[lang]['end_personal']), chat, main_menu_keyboard(chat, lang))
                elif status[0] == 2:
                    send_message(emoji.emojize(languages[lang]['end_food']), chat, main_menu_keyboard(chat, lang))
                elif status[0] == 3:
                    send_message(emoji.emojize(languages[lang]['end_activity']), chat, main_menu_keyboard(chat, lang))


def main():
    # variable para controlar el numero de mensajes
    last_update_id = None
    getMe()
    # force bd to stay clean
    db.conn.commit()
    # bucle infinito
    while True:
        # obten los mensajes no vistos
        updates = get_updates(last_update_id)
        # si hay algun mensaje do work
        try:
            if 'result' in updates and len(updates['result']) > 0:
                last_update_id = get_last_update_id(updates) + 1

                # Updates joint by user
                joint_updates = dict()
                for update in updates['result']:

                    id_ = get_chat(update)
                    if id_ in joint_updates:
                        joint_updates[id_].append(update)
                    else:
                        joint_updates[id_] = [update]

                for update in joint_updates.values():
                    t = Thread(target=handle_updates, args=(update,))
                    t.start()
                    t.join()

                # have to be gentle with the telegram server
                time.sleep(0.5)
            else:
                # if no messages lets be *more* gentle with telegram servers
                time.sleep(1)

        except Exception as e:
            print('Error ocurred, watch log!')
            log_entry(str(e))
            print(e)
            # sleep 20 seconds so the problem may solve
            time.sleep(20)



if __name__ == '__main__':
    # TODO QUESTIONS ON CACHE FOR NEXT VERSION
    init_date = datetime.datetime.now()
    # argument parser
    parser = argparse.ArgumentParser(description="Telegram BOT")
    parser.add_argument('-d', action="store_true", default=True, help="Debug mode: Print the messages on console")
    parser.add_argument('-l', action="store", default='es', help="Default languages")
    parser.add_argument('--godmode', action="store", default="wakafill", help="god mode password")
    parser.add_argument('--statistics', action="store", default="tell me your secrets",
                        help="password for getting statistics")
    spacename = parser.parse_args()

    # handler to the database
    db = DBHelper()
    # set up
    db.setup()
    # caching the number of questions
    nq_category = db.n_questions()

    # default language
    def_lang_ = spacename.l
    # debug
    debug = spacename.d
    # god mode
    god_mode = spacename.godmode.lower()
    # hidden statistics message
    statistics_word = spacename.statistics.lower()
    # languages
    languages = load_languages()
    # images
    images = load_images()
    # rules
    rules = load_rules()

    # yes / no answers
    negations = [el for el in open('strings/negations.txt', 'r').read().split('\n') if el]
    affirmations = [el for el in open('strings/affirmations.txt', 'r').read().split('\n') if el]
    # role calls -> avoid hardcodding them in different places
    roles = ['home', 'family', 'friend', 'coworker']

    TOKEN = environ['TOKEN_WAKAMOLA']
    BOT_USERNAME = environ['BOT_USERNAME_WAKAMOLA']
    # URL to interact with the API
    URL = "https://api.telegram.org/bot{}/".format(TOKEN)

    main()