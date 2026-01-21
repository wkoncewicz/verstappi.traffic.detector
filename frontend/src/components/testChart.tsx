"use client";

import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  Legend,
  ResponsiveContainer,
  BarChart
} from "recharts";
function CustomTooltip({ active, payload, label }: any) {
  if (!active || !payload || !payload.length) return null;

  const row = payload[0].payload;
  return (
    <div
      style={{
        background: "#020617",
        border: "1px solid #334155",
        padding: 10,
        borderRadius: 6,
        color: "#e5e7eb",
        fontSize: 13,
      }}
    >
      <div style={{ fontWeight: 600 }}>{label}</div>

      <div style={{ color: "#ef4444" }}>IN: {row.busesIn+row.carsIn+row.motorcyclesIn+row.trucksIn}</div>
      <div style={{ color: "#ffffff" }}>OUT: {row.busesOut+row.carsOut+row.motorcyclesOut+row.trucksOut}</div>

      <hr style={{ borderColor: "#334155", margin: "6px 0" }} />

      <div>Samochody wjeżdżające: {row.carsIn} </div>
      <div>Samochody wyjeżdżające: {row.carsOut} </div>
      <div>Ciężarówki wjeżdżające: {row.trucksIn} </div>
      <div>Ciężarówki wyjeżdżające: {row.trucksOut} </div>
      <div>Busy wjeżdżające: {row.busesIn} </div>
      <div>Busy wyjeżdżające: {row.busesOut} </div>
      <div>Motocykle wjeżdżające: {row.motorcyclesIn} </div>
      <div>Motocykle wyjeżdżające: {row.motorcyclesOut} </div>
      {/* <div>Max prędkość: {row.maxSpeed} km/h</div> */}
      {/* <div>Kamera: {row.camera}</div> */}
    </div>
  );
}

export default function BasicChart({data}:{data:any[]}) {
  return (
    <div style={{ width: "100%", height: 600 }}>
      <ResponsiveContainer>
        <LineChart data={data} margin={{ top: 10, right: 20, left: 0, bottom: 10 }}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="name" interval={0} />
          <YAxis />
          <Tooltip content={<CustomTooltip />} />
          <Legend />

          <Line type="monotone" dataKey="in" stroke="red" strokeWidth={2} dot={false} />
          <Line type='monotone' dataKey="out" stroke="white" strokeWidth={2} dot={false} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
