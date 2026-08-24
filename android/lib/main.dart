import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:http/http.dart' as http;

const channel = MethodChannel('id.nusaguard/notifications');
const apiUrl = String.fromEnvironment('API_URL', defaultValue: 'http://10.0.2.2:8000');

void main() => runApp(const NusaGuardApp());

class NusaGuardApp extends StatefulWidget { const NusaGuardApp({super.key}); @override State<NusaGuardApp> createState()=>_State(); }
class _State extends State<NusaGuardApp> {
  String status='Aktifkan akses notifikasi untuk memulai.'; bool enabled=false;
  @override void initState(){super.initState(); channel.setMethodCallHandler((call) async {if(call.method=='notificationText'){await analyze(call.arguments as String);}});}
  Future<void> grant() async {await channel.invokeMethod('openNotificationAccess'); setState(()=>enabled=true);}
  Future<void> analyze(String text) async {try{final r=await http.post(Uri.parse('$apiUrl/api/analyze'),headers:{'Content-Type':'application/json'},body:jsonEncode({'text':text,'source':'android_notification'}));final data=jsonDecode(r.body) as Map<String,dynamic>;setState(()=>status='${data['risk_level']} · ${data['category']}\n${data['recommendation']}');await channel.invokeMethod('showWarning',{'title':'NusaGuard · Risiko ${data['risk_level']}','body':'${data['category']} — ${data['recommendation']}'});}catch(_){setState(()=>status='Analisis gagal. Periksa koneksi API.');}}
  @override Widget build(BuildContext context)=>MaterialApp(debugShowCheckedModeBanner:false,theme:ThemeData(colorScheme:ColorScheme.fromSeed(seedColor:const Color(0xff1d4b3d))),home:Scaffold(appBar:AppBar(title:const Text('NusaGuard')),body:Padding(padding:const EdgeInsets.all(24),child:Column(crossAxisAlignment:CrossAxisAlignment.start,children:[const Icon(Icons.shield_outlined,size:72),const SizedBox(height:20),const Text('Peringatan penipuan, sebelum kamu bertindak',style:TextStyle(fontSize:28,fontWeight:FontWeight.bold)),const SizedBox(height:16),const Text('NusaGuard hanya membaca teks notifikasi WhatsApp baru setelah izin diberikan. Nama kontak, nomor telepon, dan histori chat tidak dikirim.'),const SizedBox(height:24),FilledButton.icon(onPressed:grant,icon:const Icon(Icons.notifications_active_outlined),label:Text(enabled?'Buka pengaturan akses':'Aktifkan akses notifikasi')),const SizedBox(height:28),Card(child:Padding(padding:const EdgeInsets.all(18),child:Text(status))) ]))));
}
