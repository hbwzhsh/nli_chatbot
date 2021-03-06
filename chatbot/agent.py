import logging

# from nltk.parse.featurechart import sent

from chatbot.parser.text_parser import TextParser
from chatbot.stt.speech_recognizer import SpeechRecognizer
from chatbot.tts.speech_agent import SpeechAgent
import config
from dialogue_act.dialogue_act import DialogueAct
from dialogue_act.dialogue_manager import DialogueManager

logging.getLogger().setLevel(logging.DEBUG)


# from dialogue_act.dialogue_manager import DialogueManager
# from dialogue_act.dialogue_mgt import DialogueActManager
class ChatBotAgent:

    def __init__(self):
        """
        Initialize speech recoginer and text to speech agent
        """
        self.da = DialogueAct()
        self.d_manager = DialogueManager()
        self.parser = TextParser()
        self.listener, self.speaker = self.init_agents()
        self.req_params = {}  # keep request and slots 
        self.res_params = {}  
        self.session = {} 
        self.filled_slots = {}
        self.has_woken_up = False

    def init_agents(self):
        self.stt = SpeechRecognizer().init_recognizer(config.STT_GOOGLE)
        self.tts = SpeechAgent().init_agent(config.TTS_PYTTSX3)
        return self.stt, self.tts

    def ask_to_fill_slot(self, empty_slot_key):
        DA_ASK_PREFIX = "ask_for_"
        respond_message = self.d_manager.get_respond_message(DA_ASK_PREFIX + empty_slot_key)
        self.speaker.speak(respond_message)
    
    def reset_session(self):
        self.req_params = {}  # keep request and slots 
        self.res_params = {}  
        self.session = {} 
        self.filled_slots = {}
        self.has_woken_up = False
    
    def init_filled_slot_obj(self, arr_slot_key):
        for key in arr_slot_key:
            self.filled_slots[key] = ""
    
    def get_empty_slot_key(self):
        for key, value in self.filled_slots.items():
            if value == "":
                return key
        return ""

    def start(self):
        # instance initialization
        # bot = ChatBotAgent()
        # dmngr = DialogueManager()

        wakeup_words = ["hi", "hello", "hey", "hey bot", "hey book bot", "hey bookbot", "bookbot"]
        end_converstion_words = ["bye", "bye bye", "goodbye", "see you"]
        greeting = False
        greeting_msg = "Hello, how may I help you?"
        goodbye_msg = "Hope to see you again soon, bye."
        
        # service name
        current_intent = {}
        
        # each round conversation
        current_action = ""
        n_slots = 0
        current_idx_slot = 0
       
        target_intent = ""
        # constant to control key
        default_cannot_extract_intent_key = "default_unrecognize_intent"
        self.speaker.speak("Now book bot is ready, please wake him up for talking")
        while True:
            try:
#                 if  greeting == False:
#                     self.speaker.speak(greeting_msg)
#                     greeting = True
 
                # Listen voice from microphone and generate sentence.
                sentence = self.listener.listen()
                if sentence.startswith("Error"):
                    continue
                
                if sentence in wakeup_words:
                    response_msg = self.d_manager.get_respond_message("response_greeting")
                    self.speaker.speak(response_msg)
                    self.has_woken_up = True
                    continue
                # recommend by author
                # sentence = "Do you have any recommended books written by Mostafa"
                
                # recommend by genre
                # sentence = "I would like to read books about psychology, do you have any recommendation"
                # recommend by genre
                # sentence = "Do you have any recommended books in psychological category"
                # find book by title
                # sentence = "Give me information about Harry Potter"
                # find book by author via google api
                # sentence = "Give me a book from Yaser Mostafa"
                
                # find book by author via ontology
                # sentence = "Give me a book from Yaser"
                
                # Check sentence with trained model for dialogue act.
                # self.speaker.speak("user asked: " + sentence)
                da_result = self.da.predict(sentence);
                print("DA type --> ", da_result)
                                # If type is end of conversation, stop program.
                
                if da_result == "Bye":  # and not is_flling_in_slot_action:
                    # TODO Jess  
                    response_msg = self.d_manager.get_respond_message("response_bye")
                    self.speaker.speak(response_msg)
                    self.reset_session()
                    continue
                
                elif da_result == "Greet":  # and not is_flling_in_slot_action:
                    response_msg = self.d_manager.get_respond_message("response_greeting")
                    self.speaker.speak(response_msg)
                    self.reset_session()
                    continue
                
                elif da_result == "whQuestion" or da_result == "ynQuestion" or da_result == "Statement" or da_result == "nAnswer" or da_result == "yAnswer":
                    # Analyze entity in question find subject, predicate, object
                    # Query in ontology by SPARQL 
                    # Generate sentence
                    # parser.get_dependency_parsing(sentence)
                    # parser.generate_response(sentence)
                    
                    is_flling_in_slot_action = 'current_action' in self.session and self.session["current_action"] == "fill_slot"
                    if is_flling_in_slot_action:
                        # fill slot from sentence
                        self.filled_slots[self.session["current_filling_slot"]] = sentence
                    
                    # curent_intent = parser.infer_intent(sentence)
                    if not 'intent' in self.session:
                        intent_obj, target_intent, max_matched_word = self.parser.get_infer_intent(sentence)
                        if target_intent == "":
                            if target_intent == "" and max_matched_word > 1:
                                # can't recognize intent but user said some matched keyword
                                response_message = self.d_manager.get_respond_message("ask_for_choices_to_find")
                                # self.session["current_action"] = "fill_slot"
                                # self.session["slots_choice"] = ["authors", "genre", "title"]
                                self.session["current_filling_slot"] = ""
                                # self.speaker.speak(response_message)
                                # self.reset_session()
                                continue
                            else:
                                # can't recognize intent
                                response_message = self.d_manager.get_respond_message(default_cannot_extract_intent_key)
                                self.speaker.speak(response_message)
                                self.reset_session()
                                continue
                        
                        else:
                            self.session["intent"] = target_intent
                            # Check there is slot to fill in.
                            slots = intent_obj["slots"]
                            self.init_filled_slot_obj(slots)
                            # Check number of slot to fill in.
                            n_slots = len(slots)
                            # Auto-filling in slot
                            auto_filled_slot = self.parser.get_auto_fill_slots(sentence, slots)
                            for key, value in auto_filled_slot.items():
                                if key in self.filled_slots:
                                    self.filled_slots[key] = value
                        
                    if target_intent.startswith("recommend") or target_intent.startswith("find"):                           
                        
                        empty_slot_key = self.get_empty_slot_key()
                        if  empty_slot_key != "":
                        # if n_slots < len(self.filled_slots):
                            self.session["current_action"] = "fill_slot"
                            # ask to fill slot
                            self.session["current_filling_slot"] = empty_slot_key
                            respond_message = self.d_manager.get_respond_message("ask_for_fill_slot_" + empty_slot_key)
                            self.speaker.speak(respond_message)
                            continue
                        else:
                            # all slot are filled.
                            # executes target request service
                            self.req_params["intent"] = target_intent
                            self.req_params["slots"] = self.filled_slots
                            # respond_msg_key = current_intent["respond_statement"]
                            response_message = self.d_manager.execute_intent(self.req_params)
                            self.speaker.speak(response_message)
                            self.reset_session()
                            # 
                
                # When user said something and bot can't understand.
                if sentence != "" and target_intent == "":
                    respond_message = self.d_manager.get_respond_message(default_cannot_extract_intent_key)
                    self.speaker.speak(respond_message)
                    continue
                # Problem, when there is no voice come, it returns error.
                # So we handle by continue
                # Continue next loop if Error is returned.
                    
                # response_msg = da.respond(sentence)
                # Call dialogue management and speak
#               # reply_message = dmngr.process(sentence)
                # speaker.speak(response_msg)

            except SystemExit:
                print("ignoring SystemExit")
            except Exception as e:
                print("Exception: " + e.__str__())
 
