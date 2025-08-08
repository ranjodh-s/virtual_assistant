from flask import Flask, render_template, request, jsonify
import action
import speech_to_text

app = Flask(__name__, template_folder='templates', static_folder='static')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/process', methods=['POST'])
def process():
    try:
        user_input = request.json.get('input')
        if not user_input:
            return jsonify({'error': 'No input provided'}), 400
        response = action.process_input(user_input)
        if response is None:
            return jsonify({'error': 'No response from action processor'}), 500
        return jsonify({'response': response})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/transcribe', methods=['POST'])
def transcribe():
    if 'audio' not in request.files:
        return jsonify({'error': 'No audio file uploaded'}), 400
    audio_file = request.files['audio']
    transcript = speech_to_text.transcribe_audio_file(audio_file)
    return jsonify({'transcript': transcript})

# Only run the server locally, not on Render (Render uses gunicorn)
if __name__ == "__main__":
    app.run(debug=True)