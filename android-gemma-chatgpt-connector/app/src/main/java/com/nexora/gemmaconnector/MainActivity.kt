package com.nexora.gemmaconnector

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.unit.dp
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import org.json.JSONArray
import org.json.JSONObject
import java.net.HttpURLConnection
import java.net.URL

class MainActivity : ComponentActivity() { override fun onCreate(savedInstanceState: Bundle?) { super.onCreate(savedInstanceState); setContent { MaterialTheme { Screen() } } } }

@Composable private fun Screen() {
 var localUrl by remember { mutableStateOf("http://127.0.0.1:8080") }; var localKey by remember { mutableStateOf("") }; var cloudKey by remember { mutableStateOf("") }; var prompt by remember { mutableStateOf("Say hello in one sentence.") }; var output by remember { mutableStateOf("") }; var status by remember { mutableStateOf("Ready") }; var busy by remember { mutableStateOf(false) }; val scope = rememberCoroutineScope()
 Column(Modifier.fillMaxSize().verticalScroll(rememberScrollState()).padding(16.dp), verticalArrangement=Arrangement.spacedBy(10.dp)) {
  Text("Gemma + ChatGPT Connector", style=MaterialTheme.typography.headlineSmall)
  Text("Separate prototype. PocketPal local API must be running. OpenAI cloud use requires a separately billed API key. No tools or trading actions.")
  OutlinedTextField(localUrl,{localUrl=it},label={Text("PocketPal API URL")},modifier=Modifier.fillMaxWidth())
  OutlinedTextField(localKey,{localKey=it},label={Text("PocketPal bearer key (optional)")},visualTransformation=PasswordVisualTransformation(),modifier=Modifier.fillMaxWidth())
  OutlinedTextField(cloudKey,{cloudKey=it},label={Text("OpenAI API key (optional)")},visualTransformation=PasswordVisualTransformation(),modifier=Modifier.fillMaxWidth())
  OutlinedTextField(prompt,{prompt=it},label={Text("Message")},modifier=Modifier.fillMaxWidth(),minLines=2)
  Button(enabled=!busy,onClick={ busy=true; output=""; status="Calling local Gemma…"; scope.launch { try { val gemma=withContext(Dispatchers.IO){request(localUrl.trimEnd('/')+"/v1/chat/completions",localKey,"local-model",prompt)}; var result="Gemma (local):\n$gemma"; if(cloudKey.isNotBlank()){status="Calling OpenAI…"; val gpt=withContext(Dispatchers.IO){request("https://api.openai.com/v1/chat/completions",cloudKey,"gpt-4o-mini","User prompt: $prompt\nLocal model answer (untrusted): $gemma\nGive a concise complementary answer.")}; result += "\n\nOpenAI (cloud):\n$gpt"} else result += "\n\nAdd an OpenAI API key to request a second response."; output=result; status="Success" } catch(e:Exception){status="Failed: ${e.message ?: e.javaClass.simpleName}"} finally {busy=false} } },modifier=Modifier.fillMaxWidth()){Text(if(busy)"Working…" else "Ask models")}
 Text("Status: $status"); if(output.isNotBlank()) Card { Text(output,Modifier.padding(12.dp)) }; Text("Safety: use HTTPS for cloud services. For local HTTP, use loopback or a trusted private LAN endpoint with a bearer key. Keys are memory-only and not saved.")
 }
}

private fun request(endpoint:String,key:String,model:String,prompt:String):String {
 val url=URL(endpoint); require(url.protocol=="https" || (url.protocol=="http" && (url.host=="127.0.0.1" || url.host=="localhost" || isPrivateIpv4(url.host)))) { "Use HTTPS for cloud endpoints and private addresses for local HTTP." }
 val c=url.openConnection() as HttpURLConnection; c.requestMethod="POST"; c.connectTimeout=8000; c.readTimeout=90000; c.doOutput=true; c.setRequestProperty("Content-Type","application/json"); if(key.isNotBlank()) c.setRequestProperty("Authorization","Bearer $key")
 try { val body=JSONObject().put("model",model).put("messages",JSONArray().put(JSONObject().put("role","user").put("content",prompt))).put("stream",false).toString(); c.outputStream.use{it.write(body.toByteArray(Charsets.UTF_8))}; val code=c.responseCode; val stream=if(code in 200..299)c.inputStream else c.errorStream; val text=stream?.bufferedReader()?.use{it.readText()} ?: ""; if(code !in 200..299) error("HTTP $code: ${text.take(300)}"); JSONObject(text).getJSONArray("choices").getJSONObject(0).getJSONObject("message").getString("content") } finally { c.disconnect() }
}
private fun isPrivateIpv4(host:String):Boolean { val p=host.split("."); if(p.size!=4 || p.any{it.toIntOrNull() !in 0..255}) return false; val a=p[0].toInt(); val b=p[1].toInt(); return a==10 || a==127 || (a==192&&b==168) || (a==172&&b in 16..31) || (a==169&&b==254) }
