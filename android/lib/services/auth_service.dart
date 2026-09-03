import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';
import '../models/auth_response.dart';
import '../models/user.dart';

const _apiUrl = String.fromEnvironment('API_URL', defaultValue: 'http://10.0.2.2:8000');

class AuthService {
  static const String _tokenKey = 'nusaguard_access_token';
  static const String _userKey = 'nusaguard_user';

  Future<AuthResponse> register(String name, String email, String password) async {
    try {
      final r = await http.post(
        Uri.parse('$_apiUrl/api/auth/register'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({'name': name, 'email': email, 'password': password}),
      );
      if (r.statusCode == 201) {
        final auth = AuthResponse.fromJson(jsonDecode(r.body) as Map<String, dynamic>);
        await _saveSession(auth);
        return auth;
      }
      final body = jsonDecode(r.body) as Map<String, dynamic>;
      throw Exception(body['detail'] as String? ?? 'Registrasi gagal');
    } on http.ClientException {
      throw Exception('Tidak dapat terhubung ke server');
    } catch (e) {
      if (e is Exception) rethrow;
      throw Exception('Tidak dapat terhubung ke server');
    }
  }

  Future<AuthResponse> login(String email, String password) async {
    try {
      final r = await http.post(
        Uri.parse('$_apiUrl/api/auth/login'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({'email': email, 'password': password}),
      );
      if (r.statusCode == 200) {
        final auth = AuthResponse.fromJson(jsonDecode(r.body) as Map<String, dynamic>);
        await _saveSession(auth);
        return auth;
      }
      if (r.statusCode == 401) {
        throw Exception('Email atau kata sandi salah');
      }
      final body = jsonDecode(r.body) as Map<String, dynamic>;
      throw Exception(body['detail'] as String? ?? 'Login gagal');
    } on http.ClientException {
      throw Exception('Tidak dapat terhubung ke server');
    } catch (e) {
      if (e is Exception) rethrow;
      throw Exception('Tidak dapat terhubung ke server');
    }
  }

  Future<void> _saveSession(AuthResponse auth) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_tokenKey, auth.accessToken);
    await prefs.setString(_userKey, jsonEncode(auth.user.toJson()));
  }

  Future<String?> getToken() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getString(_tokenKey);
  }

  Future<User?> getCurrentUser() async {
    final prefs = await SharedPreferences.getInstance();
    final data = prefs.getString(_userKey);
    if (data == null) return null;
    try {
      return User.fromJson(jsonDecode(data) as Map<String, dynamic>);
    } catch (_) {
      return null;
    }
  }

  Future<bool> isLoggedIn() async {
    return (await getToken()) != null;
  }

  Future<void> logout() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove(_tokenKey);
    await prefs.remove(_userKey);
  }

  Future<User> fetchCurrentUserFromServer() async {
    final token = await getToken();
    try {
      final r = await http.get(
        Uri.parse('$_apiUrl/api/auth/me'),
        headers: {'Authorization': 'Bearer $token'},
      );
      if (r.statusCode == 200) {
        final user = User.fromJson(jsonDecode(r.body) as Map<String, dynamic>);
        final prefs = await SharedPreferences.getInstance();
        await prefs.setString(_userKey, jsonEncode(user.toJson()));
        return user;
      }
      if (r.statusCode == 401) {
        await logout();
        throw Exception('Sesi berakhir, silakan login kembali');
      }
      throw Exception('Gagal memuat data user');
    } on http.ClientException {
      throw Exception('Tidak dapat terhubung ke server');
    } catch (e) {
      if (e is Exception) rethrow;
      throw Exception('Tidak dapat terhubung ke server');
    }
  }
}
