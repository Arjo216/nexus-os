"use client";
import React, { useEffect, useState } from 'react';
import { Canvas } from '@react-three/fiber';
import { OrbitControls, Stars, Box } from '@react-three/drei';
import { io } from 'socket.io-client';

export default function DigitalTwin() {
  const [isAlarm, setIsAlarm] = useState(false);

  useEffect(() => {
    // Connect to our WebSocket Bridge
    const socket = io('https://crispy-train-v6vw7rpjrx9gh6pqw-5000.app.github.dev/');
    
    socket.on('anomaly_detected', (data) => {
      console.log("3D Twin Received Alert:", data);
      setIsAlarm(true);
      setTimeout(() => setIsAlarm(false), 2000); // Reset after 2 seconds
    });

    return () => { socket.disconnect(); };
  }, []);

  return (
    <main className="h-screen w-full bg-slate-950">
      <div className="absolute top-10 left-10 z-10 text-white font-mono">
        <h1 className="text-3xl font-bold tracking-tighter">NEXUS :: DIGITAL TWIN</h1>
        <p className={isAlarm ? "text-red-500 animate-pulse" : "text-emerald-400"}>
          STATUS: {isAlarm ? "CRITICAL ANOMALY DETECTED" : "SYSTEMS NOMINAL"}
        </p>
      </div>

      <Canvas camera={{ position: [5, 5, 5] }}>
        <color attach="background" args={['#020617']} />
        <Stars radius={100} depth={50} count={5000} factor={4} saturation={0} fade speed={1} />
        <ambientLight intensity={0.5} />
        <pointLight position={[10, 10, 10]} />
        
        {/* Our "Sensor" represented as a 3D Building */}
        <Box args={[1, 4, 1]} position={[0, 2, 0]}>
          <meshStandardMaterial color={isAlarm ? "#ef4444" : "#10b981"} emissive={isAlarm ? "#ef4444" : "#10b981"} emissiveIntensity={isAlarm ? 2 : 0.5} />
        </Box>

        <gridHelper args={[20, 20, 0xffffff, 0x334155]} />
        <OrbitControls />
      </Canvas>
    </main>
  );
}