from flask import Flask, request, jsonify
from flask_cors import CORS
from models import SentimentAnalyzer
from aspect_extractor import AspectExtractor
from preprocessor import TextPreprocessor
import json

app = Flask(__name__)
CORS(app)

# Initialize components
sentiment_analyzer = SentimentAnalyzer()
aspect_extractor = AspectExtractor()
preprocessor = TextPreprocessor()

@app.route('/api/compare', methods=['POST'])
def compare_products():
    try:
        data = request.get_json()
        products = data.get('products', [])
        
        if len(products) < 2:
            return jsonify({'error': 'At least 2 products required'}), 400
        
        results = {
            'products': products,
            'comparison': {
                'overall': [],
                'aspects': [],
                'radarData': [],
                'reviews': {},
                'strengths': {},
                'weaknesses': {}
            }
        }
        
        # Analyze each product
        for product in products:
            # Get reviews (mock data for now)
            reviews = get_product_reviews(product)
            
            # Analyze sentiment and aspects
            analysis = analyze_product(product, reviews)
            
            results['comparison']['overall'].append({
                'name': product,
                'score': analysis['overall_score'],
                'sentiment': analysis['overall_sentiment']
            })
            
            results['comparison']['reviews'][product] = analysis['sample_reviews']
            results['comparison']['strengths'][product] = analysis['strengths']
            results['comparison']['weaknesses'][product] = analysis['weaknesses']
        
        # Build aspect comparison
        aspects = ['Camera', 'Battery', 'Performance', 'Display', 'Value', 'Build Quality']
        results['comparison']['aspects'] = build_aspect_comparison(products, aspects)
        results['comparison']['radarData'] = results['comparison']['aspects']
        
        # Determine winner
        results['comparison']['winner'] = max(
            results['comparison']['overall'],
            key=lambda x: x['score']
        )['name']
        
        return jsonify(results)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


def get_product_reviews(product_name):
    """
    In production: Scrape from Flipkart/Amazon
    For now: Return mock reviews
    """
    mock_reviews = {
        'hindi': [
            "कैमरा बहुत बढ़िया है, फोटो क्वालिटी शानदार",
            "बैटरी बैकअप थोड़ा कम है",
            "परफॉर्मेंस एकदम जबरदस्त",
            "डिस्प्ले बहुत अच्छा है",
            "कीमत थोड़ी ज्यादा है"
        ],
        'marathi': [
            "कॅमेरा खूप छान आहे",
            "बॅटरी बॅकअप कमी आहे",
            "परफॉर्मन्स उत्तम आहे"
        ]
    }
    return mock_reviews


def analyze_product(product_name, reviews):
    """Analyze all reviews for a product"""
    
    all_reviews = reviews['hindi'] + reviews['marathi']
    
    # Sentiment analysis
    sentiments = []
    aspect_sentiments = {
        'Camera': [], 'Battery': [], 'Performance': [],
        'Display': [], 'Value': [], 'Build Quality': []
    }
    
    for review in all_reviews:
        # Preprocess
        clean_text = preprocessor.clean_text(review)
        
        # Get sentiment
        sentiment_score = sentiment_analyzer.predict(clean_text)
        sentiments.append(sentiment_score)
        
        # Extract aspects
        aspects = aspect_extractor.extract_aspects(clean_text)
        for aspect in aspects:
            if aspect in aspect_sentiments:
                aspect_sentiments[aspect].append(sentiment_score)
    
    # Calculate scores
    overall_score = sum(sentiments) / len(sentiments) * 10
    
    # Aspect scores
    aspect_scores = {}
    for aspect, scores in aspect_sentiments.items():
        if scores:
            avg_score = sum(scores) / len(scores)
            aspect_scores[aspect] = int(avg_score * 100)
        else:
            aspect_scores[aspect] = 50  # neutral
    
    # Identify strengths and weaknesses
    sorted_aspects = sorted(aspect_scores.items(), key=lambda x: x[1], reverse=True)
    strengths = [asp[0] for asp in sorted_aspects[:3] if asp[1] > 70]
    weaknesses = [asp[0] for asp in sorted_aspects[-3:] if asp[1] < 60]
    
    return {
        'overall_score': round(overall_score, 1),
        'overall_sentiment': 'positive' if overall_score > 6 else 'neutral' if overall_score > 4 else 'negative',
        'aspect_scores': aspect_scores,
        'sample_reviews': [
            {'text': all_reviews[0], 'rating': 5, 'aspect': 'Camera'},
            {'text': all_reviews[1], 'rating': 3, 'aspect': 'Battery'},
            {'text': all_reviews[2], 'rating': 5, 'aspect': 'Performance'}
        ],
        'strengths': strengths if strengths else ['Overall Performance'],
        'weaknesses': weaknesses if weaknesses else ['Price Point']
    }


def build_aspect_comparison(products, aspects):
    """Build comparison data for charts"""
    comparison = []
    for aspect in aspects:
        row = {'aspect': aspect}
        for product in products:
            # Mock scores - replace with actual analysis
            import random
            row[product] = random.randint(60, 90)
        comparison.append(row)
    return comparison


@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy', 'version': '1.0.0'})


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)