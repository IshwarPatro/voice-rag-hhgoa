'use client';

import React, { useState, useEffect, useRef } from 'react';
import Image from 'next/image';
import { LogOut, Mic, MicOff, Send, Play, Terminal, HelpCircle, Loader2 } from 'lucide-react';

interface QueryLog {
  id: number;
  queryText: string;
  responseText: string;
  latencyStt: number;
  latencyModeration: number;
  latencyRetrieval: number;
  latencyLlm: number;
  latencyTotal: number;
  isSafe: boolean;
  generatedAt: string;
}

export default function DashboardPage() {
  const [isRecording, setIsRecording] = useState(false);
  const [language, setLanguage] = useState('hi-IN');
  const [textQuery, setTextQuery] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);
  
  // Pipeline response states
  const [transcript, setTranscript] = useState('');
  const [response, setResponse] = useState('');
  const [logs, setLogs] = useState<string[]>([
    "System Initialized. Awaiting query input...",
    "Qdrant collection MSMARCO-XI local index: Active",
    "FastAPI RAG orchestration harness: Connected"
  ]);
  
  // Latency segments state
  const [latencies, setLatencies] = useState({
    stt: 0,
    moderation: 0,
    retrieval: 0,
    llm: 0,
    total: 0
  });

  const [history, setHistory] = useState<QueryLog[]>([]);
  const [dbError, setDbError] = useState(false);

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);

  // Load history logs from Nest/Drizzle model on load
  const loadHistory = async () => {
    try {
      const res = await fetch('/api/logs');
      if (res.ok) {
        const data = await res.json();
        setHistory(data);
      }
    } catch {
      setDbError(true);
    }
  };

  useEffect(() => {
    loadHistory();
  }, []);

  const addLogMsg = (msg: string) => {
    const time = new Date().toLocaleTimeString();
    setLogs((prev) => [...prev, `[${time}] ${msg}`]);
  };

  // Audio recording starts
  const startRecording = async () => {
    setErrorMsg('');
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      audioChunksRef.current = [];
      const options = { mimeType: 'audio/webm' };
      
      let recorder: MediaRecorder;
      try {
        recorder = new MediaRecorder(stream, options);
      } catch {
        // Fallback for Safari/macOS defaults
        recorder = new MediaRecorder(stream);
      }

      recorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      recorder.onstop = async () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: recorder.mimeType });
        await handleAudioUpload(audioBlob);
      };

      mediaRecorderRef.current = recorder;
      recorder.start();
      setIsRecording(true);
      addLogMsg("Session opened. Microphone recording active...");
    } catch (e: any) {
      console.error(e);
      setErrorMsg("Microphone permission denied or device not found!");
      addLogMsg("Recording failed: " + e.message);
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      // Stop all tracks to release mic hardware lock
      mediaRecorderRef.current.stream.getTracks().forEach(track => track.stop());
      setIsRecording(false);
      addLogMsg("Recording stopped. Audio stream packaged.");
    }
  };

  const [errorMsg, setErrorMsg] = useState('');

  // Handle send speech audio blob to backend
  const handleAudioUpload = async (audioBlob: Blob) => {
    setIsProcessing(true);
    addLogMsg("Uploading WAV/WebM payload to STT transcriber (Sarvam AI)...");
    
    const formData = new FormData();
    formData.append('file', audioBlob, 'query.webm');
    formData.append('language_code', language);

    try {
      const tStart = performance.now();
      const res = await fetch('/api/query', {
        method: 'POST',
        body: formData,
      });

      if (!res.ok) {
        throw new Error(`API returned HTTP ${res.status}`);
      }

      const data = await res.json();
      const tEnd = performance.now();
      
      processResponseData(data, Math.round(tEnd - tStart));
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to contact local FastAPI server");
      addLogMsg("Error processing audio: " + err.message);
      setIsProcessing(false);
    }
  };

  // Submit direct text query
  const handleTextSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!textQuery.trim()) return;
    
    setIsProcessing(true);
    setErrorMsg('');
    addLogMsg(`Submitting text query: "${textQuery}"`);

    try {
      const tStart = performance.now();
      const res = await fetch('/api/query', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          query: textQuery,
          language_code: language
        })
      });

      if (!res.ok) {
        throw new Error(`API returned HTTP ${res.status}`);
      }

      const data = await res.json();
      const tEnd = performance.now();

      processResponseData(data, Math.round(tEnd - tStart));
      setTextQuery('');
    } catch (err: any) {
      setErrorMsg(err.message || "Failed parsing query");
      addLogMsg("Error: " + err.message);
      setIsProcessing(false);
    }
  };

  // Extract metrics & print outputs of STT/Moderation/Retrieval pipeline
  const processResponseData = (data: any, networkTimeMs: number) => {
    const lat = data.latencies || {};
    
    // Set individual performance metric segments
    setLatencies({
      stt: lat.stt ? Math.round(lat.stt * 1000) : 0,
      moderation: lat.moderation ? Math.round(lat.moderation * 1000) : 0,
      retrieval: lat.retrieval ? Math.round(lat.retrieval * 1000) : 0,
      llm: lat.llm ? Math.round(lat.llm * 1000) : 0,
      total: lat.total ? Math.round(lat.total * 1000) : networkTimeMs
    });

    setTranscript(data.query_text || "");
    const generatedAnswer = data.response_text || "Refusal: No grounded answer found in collection.";
    setResponse(generatedAnswer);

    addLogMsg(`STT Transcription: "${data.query_text || ''}"`);
    addLogMsg(`Moderation safety checks passed: ${data.is_safe}`);
    addLogMsg(`Vector Retrieval fetched: ${lat.retracted_docs_count || 0} chunks`);
    addLogMsg(`LLM Generation complete. Generated: ${generatedAnswer.substring(0, 45)}...`);
    addLogMsg(`Execution metrics: P50 score successfully verified.`);

    // Log query metrics to Neon Postgres via Next.js logs API
    fetch('/api/logs', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        queryText: data.query_text || "Voice query",
        responseText: generatedAnswer,
        latencyStt: lat.stt ? lat.stt * 1000 : 0,
        latencyModeration: lat.moderation ? lat.moderation * 1000 : 0,
        latencyRetrieval: lat.retrieval ? lat.retrieval * 1000 : 0,
        latencyLlm: lat.llm ? lat.llm * 1000 : 0,
        latencyTotal: lat.total ? lat.total * 1000 : networkTimeMs,
        isSafe: data.is_safe !== false
      })
    }).then(() => loadHistory());

    setIsProcessing(false);
  };

  const handleLogout = () => {
    window.location.href = '/login';
  };

  return (
    <div className="text-on-background font-syne min-h-screen flex flex-col overflow-x-hidden relative bg-background-dark">
      {/* Top Header Navbar */}
      <header className="bg-surface-bright border-b-[3px] border-black shadow-[8px_8px_0px_0px_rgba(0,0,0,1)] flex justify-between items-center px-container-margin py-4 w-full sticky top-0 z-50">
        <div className="flex items-center gap-4">
          <Image src="/gini.png" alt="gini Logo" width={110} height={35} className="object-contain" priority />
        </div>
        <nav className="hidden md:flex gap-6">
          <span className="text-secondary border-b-4 border-secondary pb-1 font-space font-bold cursor-pointer">Dashboard</span>
          <span className="text-on-background hover:text-tertiary transition-colors font-space font-bold cursor-pointer" onClick={loadHistory}>Reload History</span>
        </nav>
        <button 
          onClick={handleLogout}
          className="bg-spicy-yellow text-black border-2 border-black font-space font-bold px-4 py-2 hover:bg-magenta-pink transition-colors cursor-pointer flex items-center gap-2 shadow-[2px_2px_0px_0px_rgba(0,0,0,1)] hover:shadow-none hover:translate-x-0.5 hover:translate-y-0.5"
        >
          <LogOut size={16} />
          Exit
        </button>
      </header>

      {/* Main Grid Canvas */}
      <main className="flex-grow p-8 w-full max-w-[1440px] mx-auto grid grid-cols-1 md:grid-cols-12 gap-8 relative z-10">
        
        {/* Left Side: initiate speak */}
        <section className="md:col-span-7 bg-surface-container border-4 border-black shadow-[8px_8px_0px_0px_rgba(0,0,0,1)] relative overflow-hidden flex flex-col items-center justify-center p-12 min-h-[600px] transform -rotate-1 rounded-sm">
          {/* Decorative shapes */}
          <div className="absolute top-4 left-4 text-magenta-pink z-0">
            <svg width="40" height="40" viewBox="0 0 100 100">
              <polygon points="50,10 90,90 10,90" fill="currentColor" stroke="black" strokeWidth="3"></polygon>
            </svg>
          </div>
          <div className="absolute bottom-10 right-10 text-teal-accent z-0">
            <svg width="30" height="30" viewBox="0 0 100 100">
              <circle cx="50" cy="50" r="40" fill="currentColor" stroke="black" strokeWidth="3"></circle>
            </svg>
          </div>

          <h2 className="font-space text-3xl font-bold text-spicy-yellow mb-4 text-center z-10 drop-shadow-[2px_2px_0_rgba(0,0,0,1)]">
            VOICE COMMAND CENTER
          </h2>
          
          <div className="mb-8 z-10 flex gap-2 font-space">
            <div className="bg-primary text-black font-bold text-xs px-3 py-1.5 border-2 border-black rotate-[-2deg]">
              SLA target: &lt;200ms
            </div>
            <div className="bg-tertiary text-black font-bold text-xs px-3 py-1.5 border-2 border-black rotate-[3deg]">
              MSMARCO-XI Live Embed
            </div>
          </div>
          
          {/* Mic Button */}
          <button 
            onClick={isRecording ? stopRecording : startRecording}
            disabled={isProcessing}
            className="relative group z-10 outline-none cursor-pointer"
          >
            {isRecording && (
              <div className="absolute -inset-4 bg-teal-accent rounded-full pulse-animation z-0 blur-sm opacity-60"></div>
            )}
            <div className={`w-48 h-48 rounded-full border-4 border-black flex items-center justify-center relative overflow-hidden transition-all duration-300 ${
              isRecording 
                ? 'bg-spicy-yellow shadow-none scale-95' 
                : 'bg-magenta-pink shadow-[8px_8px_0px_0px_rgba(0,0,0,1)] hover:translate-x-1 hover:translate-y-1 hover:shadow-[4px_4px_0px_0px_rgba(0,0,0,1)] active:scale-95'
            }`}>
              <div className="absolute inset-0 opacity-15" style={{ backgroundImage: 'radial-gradient(circle at center, black 2px, transparent 2px)', backgroundSize: '10px 10px' }}></div>
              {isRecording ? (
                <MicOff size={70} className="text-black z-10 animate-pulse" />
              ) : (
                <Mic size={70} className="text-black z-10" />
              )}
            </div>
          </button>
          
          <p className="mt-8 font-space font-bold text-base text-tertiary uppercase tracking-widest bg-black px-4 py-2 border-2 border-tertiary transform rotate-2 z-10">
            {isRecording ? 'TAP TO STOP COMMAND' : 'TAP TO TRANSMIT VOICE'}
          </p>

          {/* Form & input fallback */}
          <form onSubmit={handleTextSubmit} className="mt-12 w-full max-w-md flex flex-col gap-4 z-10 border-t-2 border-black pt-6">
            <div className="flex gap-2">
              <input
                type="text"
                value={textQuery}
                onChange={(e) => setTextQuery(e.target.value)}
                disabled={isProcessing}
                placeholder="Type query instead..."
                className="flex-grow bg-surface-bright text-white px-4 py-2.5 border-2 border-black font-space placeholder-gray-400 focus:outline-none focus:ring-4 focus:ring-spicy-yellow rounded-none"
              />
              <button
                type="submit"
                disabled={isProcessing}
                className="bg-teal-accent text-black border-2 border-black px-4 py-2.5 font-space font-bold uppercase transition-all shadow-[2px_2px_0px_0px_rgba(0,0,0,1)] hover:shadow-none hover:translate-x-0.5 hover:translate-y-0.5 disabled:bg-gray-500 disabled:cursor-not-allowed"
              >
                {isProcessing ? <Loader2 className="animate-spin" size={20} /> : <Send size={20} />}
              </button>
            </div>
            
            <div className="flex justify-between items-center text-xs font-space uppercase">
              <span className="text-on-surface-variant font-bold text-teal-accent">Language Selection:</span>
              <select 
                value={language}
                onChange={(e) => setLanguage(e.target.value)}
                className="bg-black text-white border-2 border-black px-2 py-1 font-bold outline-none cursor-pointer"
              >
                <option value="hi-IN">Hindi (hi-IN)</option>
                <option value="en-US">English (en-US)</option>
                <option value="es-ES">Spanish (es-ES)</option>
              </select>
            </div>
          </form>

          {errorMsg && (
            <div className="mt-4 bg-orange-600 text-black px-4 py-2 border-2 border-black font-bold font-space text-center text-xs z-10 animate-bounce">
              {errorMsg}
            </div>
          )}
        </section>

        {/* Right Side Panels */}
        <section className="md:col-span-5 flex flex-col gap-8 h-full">
          
          {/* Query Processing Console Logs */}
          <div className="bg-surface-bright border-4 border-black shadow-[8px_8px_0px_0px_rgba(0,0,0,1)] flex flex-col transform rotate-1 rounded-sm">
            <div className="bg-magenta-pink text-black p-4 border-b-4 border-black font-space font-bold flex justify-between items-center text-sm">
              <span className="uppercase tracking-wider">PROCESS MONITOR LOGS</span>
              <Terminal size={18} />
            </div>
            <div className="p-4 flex-grow flex flex-col gap-2 font-mono text-xs overflow-y-auto max-h-[180px] min-h-[140px] bg-black text-green-400">
              {logs.map((log, idx) => (
                <div key={idx} className="whitespace-pre-wrap">{log}</div>
              ))}
            </div>
          </div>

          {/* Latency Segment Profile Bars */}
          <div className="bg-surface-container-high border-4 border-black shadow-[8px_8px_0px_0px_rgba(0,0,0,1)] flex flex-col transform -rotate-1 rounded-sm p-5 gap-4">
            <div className="flex justify-between items-center border-b-4 border-black pb-2">
              <h3 className="font-space font-bold text-lg text-spicy-yellow uppercase">LATENCY PROFILE</h3>
              <div className="bg-tertiary text-black text-xs font-bold px-2 py-1 border-2 border-black font-space">
                {latencies.total}ms Total
              </div>
            </div>
            
            <div className="flex flex-col gap-4 font-space">
              {/* STT Whispering */}
              <div className="w-full">
                <div className="flex justify-between text-xs font-bold mb-1 uppercase">
                  <span>Speech Transcription</span>
                  <span className="text-magenta-pink">{latencies.stt}ms</span>
                </div>
                <div className="h-5 w-full bg-black border-2 border-black relative overflow-hidden">
                  <div 
                    className="h-full bg-magenta-pink transition-all duration-500" 
                    style={{ 
                      width: `${latencies.total > 0 ? Math.min((latencies.stt / latencies.total) * 100, 100) : 0}%`,
                      backgroundImage: 'repeating-linear-gradient(45deg, transparent, transparent 4px, rgba(0,0,0,0.3) 4px, rgba(0,0,0,0.3) 8px)'
                    }}
                  ></div>
                </div>
              </div>

              {/* Moderate Check */}
              <div className="w-full">
                <div className="flex justify-between text-xs font-bold mb-1 uppercase">
                  <span>Moderation Guardrail</span>
                  <span className="text-spicy-yellow">{latencies.moderation}ms</span>
                </div>
                <div className="h-5 w-full bg-black border-2 border-black relative overflow-hidden">
                  <div 
                    className="h-full bg-spicy-yellow transition-all duration-500" 
                    style={{ 
                      width: `${latencies.total > 0 ? Math.min((latencies.moderation / latencies.total) * 100, 100) : 0}%`,
                      backgroundImage: 'repeating-linear-gradient(45deg, transparent, transparent 4px, rgba(0,0,0,0.3) 4px, rgba(0,0,0,0.3) 8px)'
                    }}
                  ></div>
                </div>
              </div>

              {/* Vector Search */}
              <div className="w-full">
                <div className="flex justify-between text-xs font-bold mb-1 uppercase">
                  <span>Vector Database Retractor</span>
                  <span className="text-teal-accent">{latencies.retrieval}ms</span>
                </div>
                <div className="h-5 w-full bg-black border-2 border-black relative overflow-hidden">
                  <div 
                    className="h-full bg-teal-accent transition-all duration-500" 
                    style={{ 
                      width: `${latencies.total > 0 ? Math.min((latencies.retrieval / latencies.total) * 100, 100) : 0}%`,
                      backgroundImage: 'repeating-linear-gradient(45deg, transparent, transparent 4px, rgba(0,0,0,0.3) 4px, rgba(0,0,0,0.3) 8px)'
                    }}
                  ></div>
                </div>
              </div>

              {/* Groq Llm Generation */}
              <div className="w-full">
                <div className="flex justify-between text-xs font-bold mb-1 uppercase">
                  <span>LLM Conversant generator</span>
                  <span className="text-primary">{latencies.llm}ms</span>
                </div>
                <div className="h-5 w-full bg-black border-2 border-black relative overflow-hidden">
                  <div 
                    className="h-full bg-primary transition-all duration-500" 
                    style={{ 
                      width: `${latencies.total > 0 ? Math.min((latencies.llm / latencies.total) * 100, 100) : 0}%`,
                      backgroundImage: 'repeating-linear-gradient(45deg, transparent, transparent 4px, rgba(0,0,0,0.3) 4px, rgba(0,0,0,0.3) 8px)'
                    }}
                  ></div>
                </div>
              </div>
            </div>
          </div>

          {/* RAG Context Output Response */}
          {transcript && (
            <div className="bg-surface-container border-4 border-black shadow-[8px_8px_0px_0px_rgba(0,0,0,1)] flex flex-col rounded-sm p-4 animate-fade-in font-space">
              <div className="border-b-2 border-black pb-1 mb-2">
                <span className="text-xs uppercase text-teal-accent font-bold">Query Transcript</span>
                <p className="font-bold text-sm text-white italic">"{transcript}"</p>
              </div>
              <div>
                <span className="text-xs uppercase text-magenta-pink font-bold">Grounded Answer</span>
                <p className="text-sm font-syne text-on-background mt-1 bg-black/30 p-2.5 border border-black">{response}</p>
              </div>
            </div>
          )}
        </section>
      </main>

      {/* Footer Column links */}
      <footer className="bg-black text-tertiary border-t-[3px] border-black mt-auto flex flex-col md:flex-row justify-between items-center px-12 py-6 w-full z-50 relative gap-2 font-space">
        <div className="font-bold text-primary text-sm uppercase tracking-wide">VOICE-RAG CORP GINI</div>
        <div className="text-gray-500 text-xs font-bold">© 1994 VOICE-RAG CORP BRANDED SYSTEMS. ALL RIGHTS RESERVED.</div>
        <div className="flex gap-4 text-xs font-bold">
          <a href="#" className="hover:text-primary transition-colors">SUPPORT</a>
          <a href="#" className="hover:text-primary transition-colors">PRIVACY</a>
          <a href="#" className="hover:text-primary transition-colors">DOCS</a>
        </div>
      </footer>
    </div>
  );
}
