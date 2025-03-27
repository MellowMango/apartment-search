import { AuthProvider } from '../src/contexts/AuthContext';
import { ThemeProvider } from '../src/contexts/ThemeContext';
import '../styles/globals.css';
import '../public/styles/MarkerCluster.Default.css';
import { Toaster } from '../components/ui/toaster';

function MyApp({ Component, pageProps }) {
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