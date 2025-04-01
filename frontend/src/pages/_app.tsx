import { useEffect } from 'react';
import { AppProps } from 'next/app';
import AuthContext, { AuthProvider } from '../contexts/AuthContext';
import { ThemeProvider } from '../contexts/ThemeContext';
import '../../styles/globals.css';
import 'leaflet.markercluster/dist/MarkerCluster.Default.css';
import { Toaster } from '../components/ui/toaster';

function MyApp({ Component, pageProps }: AppProps) {
  return (
    <ThemeProvider>
      <AuthProvider>
        <Component {...pageProps} />
        <Toaster />
      </AuthProvider>
    </ThemeProvider>
  );
}

export default MyApp; 