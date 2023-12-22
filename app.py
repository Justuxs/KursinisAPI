import os
from langchain.llms import OpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import ConversationChain
from langchain.retrievers import WikipediaRetriever
from langchain.chains import ConversationalRetrievalChain
from langchain.chat_models import ChatOpenAI
from flask import Flask, request, jsonify, render_template

os.environ['OPENAI_API_KEY'] = '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'

conversations = []
templatas = PromptTemplate(
    input_variables=['subject', 'scope', 'topic'],
    template="Tu esi mokytojas robotas, kuris duoda informacijos astuntokui. Dabar papasakok astuntokui apie is {subject} -> {scope} temos apie {topic}. Informacija turi buti lengvai suprantama ir nebendrauk su mokyniu;"
)
templatas_atsakyk = PromptTemplate(
    input_variables=['klausimas'],
    template="Trumpai atsakyk i mano klausima: {klausimas}. Jei klausimas yra neetiskas arba yra neiškonteksto (ne apie sia tema) atskyk - I toki kalusima negaliu atsakyti"
)

templatas_atsakymo = PromptTemplate(
    input_variables=['atsakymas'],
    template="As manau, kad atsakymas yra {atsakymas}. Pasakyk ar gerai as atsakiau. Jei blogai paiskink koks turėjo buti atsakymas ir kodėl šitas blogas."
)

template_toliau = 'Tesk pasakoti apie temą'

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
    if(conversation_id>len(conversations)):
        return jsonify({'message': 'Bad params'}), 400
    body = request.get_json()
    # Validate the body object
    if not body or not isinstance(body, dict):
        return jsonify({'error': 'Invalid body object'}), 400
    # Get the subject, scope and topic from the body object
    subject = body.get('subject')
    scope = body.get('scope')
    topic = body.get('topic')
    # Validate the subject, scope and topic
    if not subject or not scope or not topic or not isinstance(subject, str) or not isinstance(scope,str) or not isinstance(
            topic, str):
        return jsonify({'error': 'Invalid subject, scope or topic'}), 400
    # Generate a prompt using the templatas object and the subject, scope and topic

    prompt = templatas.format(subject=subject, scope=scope, topic=topic)
    print(prompt)

    response = conversations[conversation_id].run(prompt)
    print(response)

    return jsonify({'response': response}), 200

@app.route('/atsakyk/<int:conversation_id>', methods=['POST'])
def atsakyk(conversation_id):
    if(conversation_id>len(conversations)):
        return jsonify({'message': 'Bad params'}), 400
    body = request.get_json()
    # Validate the body object
    if not body or not isinstance(body, dict):
        return jsonify({'error': 'Invalid body object'}), 400

    question = body.get('question')

    # Validate the subject, scope and topic
    if not question or not isinstance(question, str):
        return jsonify({'error': 'Invalid question'}), 400

    prompt = templatas_atsakyk.format(klausimas=question)
    print(prompt)

    response = conversations[conversation_id].run(prompt)
    print(response)

    return jsonify({'response': response}), 200


# Define a controller function for the endpoint that gives more information
@app.route('/toliau/<int:conversation_id>', methods=['GET'])
def toliau(conversation_id):
    if(conversation_id>len(conversations)):
        return jsonify({'message': 'Bad params'}), 400
    response = conversations[conversation_id].run(template_toliau)
    return jsonify({'response': response}), 200


@app.route('/klausimas/<int:conversation_id>', methods=['GET'])
def klausimas(conversation_id):
    if(conversation_id>len(conversations)):
        return jsonify({'message': 'Bad params'}), 400
    response = conversations[conversation_id].run(template_klausimas)
    return jsonify({'response': response}), 200

@app.route('/atsakymas/<int:conversation_id>', methods=['POST'])
def atsakymas(conversation_id):
    if(conversation_id>len(conversations)):
        return jsonify({'message': 'Bad params'}), 400
    body = request.get_json()
    if not body or not isinstance(body, dict):
        return jsonify({'error': 'Invalid body object'}), 400
    answ = body.get('answer')
    prompt = templatas_atsakymo.format(atsakymas=answ)
    print(prompt)
    response = conversations[conversation_id].run(prompt)
    return jsonify({'response': response}), 200

@app.route('/create', methods=['POST'])
def add_conversation():
    retriever = WikipediaRetriever()

    convo = ConversationChain(llm=OpenAI(temperature=0.7))
    model = ChatOpenAI(model_name="gpt-3.5-turbo")
    qa = ConversationalRetrievalChain.from_llm(model, retriever=retriever)

    conversations.append(convo)
    return jsonify({'id': len(conversations)-1}), 201

@app.route('/stats')
def stats():
    # Calculate average request time and total conversations (replace with actual statistics)
    avg_request_time = 0.0
    total_conversations = len(conversations)
    status = "Running"

    return render_template('stadts.html', avg_request_time=avg_request_time, total_conversations=total_conversations, status=status)

@app.route('/')
def index():
    return render_template('index.html')

# Run the app
if __name__ == '__main__':
    app.run(debug=True)
