class NseaeScores {
  final double urgency;
  final double authority;
  final double fear;
  final double reward;
  final double impersonation;
  final double credentialRequest;

  NseaeScores({
    required this.urgency,
    required this.authority,
    required this.fear,
    required this.reward,
    required this.impersonation,
    required this.credentialRequest,
  });

  factory NseaeScores.fromJson(Map<String, dynamic> json) {
    return NseaeScores(
      urgency: (json['urgency'] as num).toDouble(),
      authority: (json['authority'] as num).toDouble(),
      fear: (json['fear'] as num).toDouble(),
      reward: (json['reward'] as num).toDouble(),
      impersonation: (json['impersonation'] as num).toDouble(),
      credentialRequest: (json['credential_request'] as num).toDouble(),
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'urgency': urgency,
      'authority': authority,
      'fear': fear,
      'reward': reward,
      'impersonation': impersonation,
      'credential_request': credentialRequest,
    };
  }
}

class AnalyzeResult {
  final String kategoriDasar;
  final String kategoriNusaGuard;
  final String riskLevel;
  final double riskScore;
  final double confidence;
  final NseaeScores nseaeScores;
  final String explanation;
  final String recommendedAction;

  AnalyzeResult({
    required this.kategoriDasar,
    required this.kategoriNusaGuard,
    required this.riskLevel,
    required this.riskScore,
    required this.confidence,
    required this.nseaeScores,
    required this.explanation,
    required this.recommendedAction,
  });

  factory AnalyzeResult.fromJson(Map<String, dynamic> json) {
    return AnalyzeResult(
      kategoriDasar: json['kategori_dasar'] as String,
      kategoriNusaGuard: json['kategori_nusaguard'] as String,
      riskLevel: json['risk_level'] as String,
      riskScore: (json['risk_score'] as num).toDouble(),
      confidence: (json['confidence'] as num).toDouble(),
      nseaeScores: NseaeScores.fromJson(
        json['nseae_scores'] as Map<String, dynamic>,
      ),
      explanation: json['explanation'] as String,
      recommendedAction: json['recommended_action'] as String,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'kategori_dasar': kategoriDasar,
      'kategori_nusaguard': kategoriNusaGuard,
      'risk_level': riskLevel,
      'risk_score': riskScore,
      'confidence': confidence,
      'nseae_scores': nseaeScores.toJson(),
      'explanation': explanation,
      'recommended_action': recommendedAction,
    };
  }
}
