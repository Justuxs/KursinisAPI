import os
from langchain.llms import OpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import ConversationChain
from langchain.retrievers import WikipediaRetriever
from langchain.chains import ConversationalRetrievalChain
from langchain.chat_models import ChatOpenAI
from flask import Flask, request, jsonify, render_template

os.environ['OPENAI_API_KEY'] = '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'

class ChatAI(object):
    convo = ConversationChain
    wikiConvo = ConversationalRetrievalChain
    chat_history = []
    subject = ""
    scope = ""
    topic = ""

    def __init__(self, convo=None, wikiConvo=None, chat_history=None):
        self.convo = convo if convo is not None else self.convo()
        self.wikiConvo = wikiConvo if wikiConvo is not None else self.wikiConvo()
        self.chat_history = chat_history if chat_history is not None else self.chat_history\
    
    def setTheme(self, subject, scope, topic):
        self.subject = subject
        self.scope = scope
        self.topic = topic

        
    def generate_start(self, prompt):
        response = self.convo.run(prompt)
        self.chat_history.append({"Klausimas": prompt, "Atsakymas": response})
        return response
    
    def generate_next(self, prompt):
        response = self.convo.run(prompt)
        self.chat_history.append({"Klausimas": prompt, "Atsakymas": response})
        return response

    def generate_question(self):
        response = self.convo.run(template_klausimas)
        return response
    
    def generate_question_answer(self, prompt):
        response = self.convo.run(prompt)
        return response
    
    def generate_answer(self, question):
        prompt = templatas_atsakyk.format(klausimas=question, subject=self.subject , scope=self.scope , topic=self.topic)
        print(prompt)
        result = self.wikiConvo({"question": prompt, "chat_history": []})
        return result['answer']

chat_ai = []

templatas = PromptTemplate(
    input_variables=['subject', 'scope', 'topic'],
    template="Tu esi mokytojas robotas, kuris duoda informacijos astuntokui. Dabar papasakok astuntokui apie is {subject} -> {scope} temos apie {topic}. Informacija turi buti lengvai suprantama ir nebendrauk su mokyniu;"
)
templatas_atsakyk = PromptTemplate(
    input_variables=['klausimas','subject','scope','topic'],
    template="Trumpai atsakyk i mano klausima: {klausimas}. Jei klausimas yra neetiskas arba yra neiškonteksto (ne apie šią temą {subject}-> {scope} -> {topic}) atskyk - I toki kalusima negaliu atsakyti"
)

templatas_atsakymo = PromptTemplate(
    input_variables=['atsakymas'],
    template="As manau, kad atsakymas yra {atsakymas}. Pasakyk ar gerai as atsakiau. Jei blogai paiskink koks turėjo buti atsakymas ir kodėl šitas blogas."
)

template_toliau = 'Tesk pasakoti apie čią temą'

template_klausimas = 'Is tavo duotos informacijos sugeneruok 1 klausimą su 4 atsakymais A B C D iskuriu tik vienas tesingas, o 3 neteisingi. Informacija pateik tokiu json formatu {' \
                      '"klausimas": "", ' \
                      '"atsakymai": {' \
                      '"A": "", ' \
                      '"B": " ", ' \
                      '"C": "", ' \
                      '"D": ""' \
                      '}, ' \
                      '"teisingas_atsakymas": ""' \
                      '}'

# Import the Flask module

app = Flask(__name__)

# Define a controller function for the endpoint that takes a body object
@app.route('/generuok/<int:conversation_id>', methods=['POST'])
def controller(conversation_id):
    if(conversation_id>len(chat_ai)):
        return jsonify({'message': 'Bad params'}), 400
    body = request.get_json()
    if not body or not isinstance(body, dict):
        return jsonify({'error': 'Invalid body object'}), 400
    subject = body.get('subject')
    scope = body.get('scope')
    topic = body.get('topic')
    
    if not subject or not scope or not topic or not isinstance(subject, str) or not isinstance(scope,str) or not isinstance(
            topic, str):
        return jsonify({'error': 'Invalid subject, scope or topic'}), 400
    
    prompt = templatas.format(subject=subject, scope=scope, topic=topic)
    print(prompt)
    chat_ai[conversation_id].setTheme(subject,scope,topic)
    response = chat_ai[conversation_id].generate_start(prompt)
    
    print(response)

    return jsonify({'response': response}), 200

@app.route('/atsakyk/<int:conversation_id>', methods=['POST'])
def atsakyk(conversation_id):
    if(conversation_id>len(chat_ai)):
        return jsonify({'message': 'Bad params'}), 400
    body = request.get_json()
    if not body or not isinstance(body, dict):
        return jsonify({'error': 'Invalid body object'}), 400

    question = body.get('question')

    if not question or not isinstance(question, str):
        return jsonify({'error': 'Invalid question'}), 400

    response = chat_ai[conversation_id].generate_answer(question)
    print(response)

    return jsonify({'response': response}), 200


# Define a controller function for the endpoint that gives more information
@app.route('/toliau/<int:conversation_id>', methods=['GET'])
def toliau(conversation_id):
    if(conversation_id>len(chat_ai)):
        return jsonify({'message': 'Bad params'}), 400
    response = chat_ai[conversation_id].generate_next(template_toliau)
    return jsonify({'response': response}), 200


@app.route('/klausimas/<int:conversation_id>', methods=['GET'])
def klausimas(conversation_id):
    if(conversation_id>len(chat_ai)):
        return jsonify({'message': 'Bad params'}), 400
    response = chat_ai[conversation_id].generate_question()
    return jsonify({'response': response}), 200

@app.route('/atsakymas/<int:conversation_id>', methods=['POST'])
def atsakymas(conversation_id):
    if(conversation_id>len(chat_ai)):
        return jsonify({'message': 'Bad params'}), 400
    body = request.get_json()
    if not body or not isinstance(body, dict):
        return jsonify({'error': 'Invalid body object'}), 400
    answ = body.get('answer')
    prompt = templatas_atsakymo.format(atsakymas=answ)
    print(prompt)
    response = chat_ai[conversation_id].generate_question_answer(prompt)
    return jsonify({'response': response}), 200

@app.route('/create', methods=['POST'])
def add_conversation():
    retriever = WikipediaRetriever()
    convo = ConversationChain(llm=OpenAI(temperature=0.5))
    model = ChatOpenAI(model_name="gpt-3.5-turbo")
    wikiConvo = ConversationalRetrievalChain.from_llm(model, retriever=retriever)
    chat_historiy = []
    chat_ai_instance = ChatAI(convo=convo, wikiConvo=wikiConvo, chat_history=chat_historiy)
    chat_ai.append(chat_ai_instance)
    return jsonify({'id': len(chat_ai)-1}), 201

@app.route('/ping', methods=['GET'])
def ping():
    
    return jsonify({'answer': "pong"}), 201

@app.route('/stats')
def stats():
    # Calculate average request time and total conversations (replace with actual statistics)
    avg_request_time = 0.0
    total_conversations = len(chat_ai)
    status = "Running"

    return render_template('stadts.html', avg_request_time=avg_request_time, total_conversations=total_conversations, status=status)

@app.route('/')
def index():
    return render_template('index.html')

@app.errorhandler(Exception)
def handle_error(error):
    response = {'error': str(error)}
    return jsonify(response), 500 
# Run the app
if __name__ == '__main__':
    app.run(debug=True)
