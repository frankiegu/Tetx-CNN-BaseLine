from flask import Flask, jsonify, request
from flask_restful import Resource, Api
import os
import tensorflow as tf
import numpy as np
import tensorflow.contrib.keras as kr
from model.cnn_model import TCNNConfig, TextCNN
from model.data_processing import read_category, read_vocab
import json
app = Flask(__name__)
api = Api(app)
# 返回的json支持中文
app.config['JSON_AS_ASCII'] = False
# os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'
def global_():
    # 全局定义和全局加载模型，提升inference速度
    global base_dir, vocab_dir, save_dir, save_path, graph, model
    base_dir = 'data/data'
    vocab_dir = os.path.join(base_dir, 'vocab.txt')
    save_dir = 'checkpoints/textcnn'
    save_path = os.path.join(save_dir, 'best_validation')
    graph = tf.get_default_graph()
    model = CnnModel()
class CnnModel:
    def __init__(self):
        self.config = TCNNConfig()
        self.categories, self.cat_to_id = read_category()
        self.words, self.word_to_id = read_vocab(vocab_dir)
        self.config.vocab_size = len(self.words)
        self.model = TextCNN(self.config)
        self.session = tf.Session()
        self.session.run(tf.global_variables_initializer())
        saver = tf.train.Saver()
        saver.restore(sess=self.session, save_path=save_path)
    def emotion_score(self, message):
        data = [self.word_to_id[x] for x in message if x in self.word_to_id]
        feed_dict = {
            self.model.input_x: kr.preprocessing.sequence.pad_sequences([data], self.config.seq_length),
            self.model.keep_prob: 1.0}
        # 类别概率的输出
        predictions = self.session.run(self.model.softmax_tensor1, feed_dict=feed_dict)
        return np.squeeze(predictions)[1]
global_()
@app.route("/sentiment_analysis_api", methods=['POST'])
def predict():
    data = json.loads(request.get_data().decode('utf-8'))
    content = data['content']
    with graph.as_default():
        sa = model.emotion_score(content)
        result = {'comment': content, 'sa': ("%.5f" % sa)}
        return jsonify(result)
if __name__ == '__main__':
    app.run(threaded=True)