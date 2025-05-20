import csv
import math
from flask import Flask, render_template, request

app = Flask(__name__)

class PostOfficeFinder:
    def __init__(self):
        self.offices = self._load_data()
        self.pincode_index = {o['pincode']: o for o in self.offices}
        self.name_index = {o['officename'].lower(): o for o in self.offices}
    
    def _load_data(self):
        """Robust data loader with validation"""
        offices = []
        try:
            with open('data/post_offices.csv', 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                next(reader)  # Skip header
                for row in reader:
                    if len(row) >= 4:
                        try:
                            offices.append({
                                'officename': row[0].strip(),
                                'pincode': row[1].strip(),
                                'coords': (float(row[2]), float(row[3]))
                            })
                        except ValueError:
                            continue
            return offices
        except Exception as e:
            print(f"Data loading error: {e}")
            return []

    def _custom_similarity(self, str1, str2):
        """Library-free fuzzy matching (0-1 scale)"""
        if not str1 or not str2:
            return 0.0
            
        str1 = str1.lower().replace("gpo", "").replace("post office", "").strip()
        str2 = str2.lower().replace("gpo", "").replace("post office", "").strip()
        
        # Exact match
        if str1 == str2:
            return 1.0
            
        # Common abbreviations (e.g. "lko" for "lucknow")
        common_abbr = {
            'mum': 'mumbai',
            'lko': 'lucknow',
            'del': 'delhi',
            'chn': 'chennai',
            'kol': 'kolkata',
            'hyd': 'hyderabad'
        }
        if str1 in common_abbr and common_abbr[str1] in str2:
            return 0.9
            
        # Contains match
        if str1 in str2 or str2 in str1:
            return 0.7
            
        # Character-based similarity
        match_chars = 0
        min_len = min(len(str1), len(str2))
        for i in range(min_len):
            if str1[i] == str2[i]:
                match_chars += 1
        char_sim = match_chars / max(len(str1), len(str2))
        
        # Word overlap
        words1 = set(str1.split())
        words2 = set(str2.split())
        word_sim = len(words1 & words2) / max(len(words1), 1)
        
        return max(char_sim, word_sim * 0.7)
    
    def search(self, name="", pincode=""):
        """Error-tolerant search with optional fields"""
        results = []
        
        # Phase 1: Exact matches (PIN takes priority)
        if pincode and pincode in self.pincode_index:
            return [{
                'office': self.pincode_index[pincode],
                'score': 1.0,
                'match_type': 'exact_pin'
            }]
            
        if name and name.lower() in self.name_index:
            return [{
                'office': self.name_index[name.lower()],
                'score': 1.0,
                'match_type': 'exact_name'
            }]
        
        # Phase 2: Fuzzy matches
        if pincode:
            # Partial PIN matches (e.g. "226" for Lucknow)
            for office in self.offices:
                if office['pincode'].startswith(pincode):
                    results.append({
                        'office': office,
                        'score': 0.8 - (0.1 * (6 - len(pincode))),  # Longer partial = better
                        'match_type': 'partial_pin'
                    })
        
        if name:
            # Name-based fuzzy matches
            for office in self.offices:
                score = self._custom_similarity(name, office['officename'])
                if score > 0.2:  # Low threshold to be forgiving
                    results.append({
                        'office': office,
                        'score': score,
                        'match_type': 'fuzzy_name'
                    })
        
        # Phase 3: Fallback - return all offices if no matches
        if not results and not pincode and not name:
            results = [{
                'office': office,
                'score': 0.1,
                'match_type': 'fallback'
            } for office in self.offices[:10]]  # Limit to first 10
        
        # Deduplicate and sort
        seen = set()
        final_results = []
        for r in sorted(results, key=lambda x: x['score'], reverse=True):
            if r['office']['pincode'] not in seen:
                seen.add(r['office']['pincode'])
                final_results.append(r)
                if len(final_results) >= 5:  # Limit results
                    break
        
        return final_results

finder = PostOfficeFinder()

@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        pincode = request.form.get("pincode", "").strip()
        
        # PIN code validation
        if pincode and (not pincode.isdigit() or len(pincode) > 6):
            return render_template("index.html",
                                error="PIN must be up to 6 digits",
                                name=name,
                                pincode=pincode)
        
        results = finder.search(name, pincode)
        return render_template("results.html",
                            results=results,
                            name_query=name,
                            pincode_query=pincode)
    
    return render_template("index.html")

if __name__ == "__main__":
    app.run(debug=True, port=5001)