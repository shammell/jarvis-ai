'use client'

import React, { useState, useEffect, useRef } from 'react'

export default function Dashboard() {
  const [logs, setLogs] = useState<string[]>([
    'Initializing JARVIS System...',
    'Loading Neural Modules...',
    'Checking Hardware Integrity...',
    'Establishing gRPC Connection...',
    'System Online. Monitoring active.'
  ])
  const [status, setStatus] = useState({
    backend: 'online',
    voice: 'online',
    api: 'online'
  })
  const [mounted, setMounted] = useState(false)
  const [dateStr, setDateStr] = useState('')
  const [sessionStr, setSessionStr] = useState('')
  const logEndRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    setMounted(true)
    setDateStr(new Date().toLocaleDateString())
    setSessionStr(Math.random().toString(36).substring(7).toUpperCase())
  }, [])

  useEffect(() => {
    const interval = setInterval(() => {
      const newLog = `[${new Date().toLocaleTimeString()}] Processing: ${Math.random() > 0.5 ? 'Optimizing Neural Weights' : 'Scanning Sensor Data'}...`
      setLogs(prev => [...prev.slice(-100), newLog])
    }, 3000)
    return () => clearInterval(interval)
  }, [])

  useEffect(() => {
    if (logEndRef.current) {
      logEndRef.current.scrollIntoView({ behavior: 'smooth' })
    }
  }, [logs])

  return (
    <div className="bg-black text-cyan-400 h-screen w-screen overflow-hidden flex flex-col font-mono p-4 select-none">
      {/* Header */}
      <div className="flex justify-between items-center border-b border-cyan-900 pb-2 mb-4">
        <h1 className="text-2xl font-bold tracking-widest text-cyan-500">THE EYE | JARVIS</h1>
        <div className="text-sm">
          DATE: {mounted ? dateStr : '--------'} | CLASSIFIED: LEVEL 5
        </div>
      </div>

      <div className="flex-1 grid grid-cols-12 gap-4 h-full overflow-hidden">
        {/* Left Column: Vitals */}
        <div className="col-span-3 flex flex-col gap-4">
          <VitalCard title="BACKEND" status={status.backend} />
          <VitalCard title="VOICE" status={status.voice} />
          <VitalCard title="API GATEWAY" status={status.api} />

          <div className="mt-auto border border-cyan-900 p-4 bg-gray-900/30">
            <h3 className="text-xs mb-2 text-cyan-600">SYSTEM ARCHITECTURE</h3>
            <div className="text-[10px] space-y-1 opacity-70">
              <p>HYBRID-CLOUD: ACTIVE</p>
              <p>LATENCY: 12ms</p>
              <p>THROUGHPUT: 4.2GB/s</p>
              <p>UPTIME: 99.998%</p>
            </div>
          </div>
        </div>

        {/* Center Column: System Orb */}
        <div className="col-span-6 flex flex-col items-center justify-center relative">
          <div className="absolute inset-0 flex items-center justify-center opacity-20">
            <div className="w-[500px] h-[500px] border border-cyan-900 rounded-full animate-spin-slow"></div>
            <div className="absolute w-[400px] h-[400px] border border-cyan-800 rounded-full animate-reverse-spin-slow"></div>
          </div>

          <div className="relative group">
            {/* The Orb */}
            <div className="w-64 h-64 rounded-full bg-gradient-to-br from-cyan-400 to-blue-600 shadow-[0_0_60px_rgba(34,211,238,0.5)] animate-pulse relative z-10 flex items-center justify-center">
              <div className="w-56 h-56 rounded-full bg-black flex items-center justify-center">
                <div className="w-48 h-48 rounded-full bg-gradient-to-t from-cyan-900 via-transparent to-cyan-400/20 flex items-center justify-center overflow-hidden">
                  <div className="text-center">
                    <div className="text-4xl font-black text-cyan-400">J</div>
                    <div className="text-[10px] font-bold text-cyan-500">LISTENING</div>
                  </div>
                </div>
              </div>
            </div>

            {/* Pulse effect */}
            <div className="absolute top-0 left-0 w-64 h-64 rounded-full border-2 border-cyan-400 animate-ping opacity-20"></div>
          </div>

          <div className="mt-12 text-center">
            <p className="text-xl font-bold tracking-[0.5em] text-cyan-300">CORE ACTIVE</p>
            <div className="mt-2 flex gap-1 justify-center">
              {[...Array(10)].map((_, i) => (
                <div key={i} className={`h-1 w-4 bg-cyan-600 animate-pulse`} style={{ animationDelay: `${i * 100}ms` }}></div>
              ))}
            </div>
          </div>
        </div>

        {/* Right Column: Console */}
        <div className="col-span-3 flex flex-col border border-cyan-900 bg-black/50 overflow-hidden">
          <div className="bg-cyan-950 px-3 py-1 text-xs font-bold flex justify-between">
            <span>THINKING CONSOLE</span>
            <span className="animate-pulse">● LIVE</span>
          </div>
          <div className="flex-1 overflow-y-auto p-3 text-[11px] leading-relaxed scrollbar-hide">
            {logs.map((log, i) => (
              <div key={i} className="mb-1 border-l border-cyan-800 pl-2">
                <span className="text-cyan-700 mr-2">{'>'}</span>
                {log}
              </div>
            ))}
            <div ref={logEndRef} />
          </div>
        </div>
      </div>

      {/* Footer Info */}
      <div className="mt-4 flex justify-between text-[10px] text-cyan-800 border-t border-cyan-900 pt-2">
        <div>COORDINATES: 37.7749° N, 122.4194° W</div>
        <div>SESSION: {mounted ? sessionStr : '--------'}</div>
        <div>ELON-TIER AUTONOMY: ENABLED</div>
      </div>

      <style jsx global>{`
        @keyframes spin-slow {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
        @keyframes reverse-spin-slow {
          from { transform: rotate(360deg); }
          to { transform: rotate(0deg); }
        }
        .animate-spin-slow {
          animation: spin-slow 20s linear infinite;
        }
        .animate-reverse-spin-slow {
          animation: reverse-spin-slow 25s linear infinite;
        }
        .scrollbar-hide::-webkit-scrollbar {
          display: none;
        }
        .scrollbar-hide {
          -ms-overflow-style: none;
          scrollbar-width: none;
        }
      `}</style>
    </div>
  )
}

function VitalCard({ title, status }: { title: string; status: string }) {
  return (
    <div className="border border-cyan-900 p-3 bg-gray-900/40 relative overflow-hidden group">
      <div className="absolute top-0 right-0 w-16 h-16 bg-cyan-400/5 rotate-45 translate-x-8 -translate-y-8 group-hover:bg-cyan-400/10 transition-colors"></div>
      <h2 className="text-xs font-bold text-cyan-700 mb-1">{title}</h2>
      <div className="flex items-center justify-between">
        <span className="text-lg font-black tracking-widest">{status.toUpperCase()}</span>
        <div className={`w-2 h-2 rounded-full ${status === 'online' ? 'bg-cyan-400 shadow-[0_0_8px_#22d3ee]' : 'bg-red-500 shadow-[0_0_8px_#ef4444]'} animate-pulse`}></div>
      </div>
      <div className="mt-2 h-1 w-full bg-cyan-950 overflow-hidden">
        <div className="h-full bg-cyan-500 w-[70%] animate-pulse"></div>
      </div>
    </div>
  )
}
