import React from 'react';

export default function TestPage() {
  return (
    <div style={{ padding: '2rem', maxWidth: '800px', margin: '0 auto' }}>
      <h1>Test Page</h1>
      <p>This is a test page to verify routing is working.</p>
      <ul>
        <li><a href="/">Home</a></li>
        <li><a href="/map">Map</a></li>
        <li><a href="/about">About</a></li>
      </ul>
    </div>
  );
} 