import { useEffect, useState } from 'react';
import Link from 'next/link';
import Layout from '../components/Layout';
import { fetchProperties } from '../../lib/supabase';

export default function Home() {
  const [properties, setProperties] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadProperties() {
      try {
        setLoading(true);
        // Fetch properties using our utility function - include those with missing coordinates
        const data = await fetchProperties({ 
          sortBy: 'created_at', 
          sortAsc: false,
          pageSize: 9,
          page: 1,
          filters: {},
          includeIncomplete: true, // Show properties even if they have missing coordinates
          includeResearch: true
        });
        
        console.log(`Loaded ${data.length} properties for homepage`);
        setProperties(data);
      } catch (error) {
        console.error('Error fetching properties:', error);
      } finally {
        setLoading(false);
      }
    }

    loadProperties();
  }, []);

  return (
    <Layout title="Austin Multifamily Property Listing Map">
      {/* Hero Section */}
      <section className="relative bg-blue-600 text-white">
        <div className="absolute inset-0 bg-gradient-to-br from-blue-700 to-blue-500 opacity-90"></div>
        <div className="relative max-w-7xl mx-auto px-4 py-24 sm:px-6 lg:py-32 lg:px-8 flex flex-col items-center">
          <div className="absolute top-0 left-0 w-full h-full bg-opacity-10 bg-white" style={{ backgroundImage: "url('data:image/svg+xml,%3Csvg width='100' height='100' viewBox='0 0 100 100' xmlns='http://www.w3.org/2000/svg'%3E%3Cpath d='M11 18c3.866 0 7-3.134 7-7s-3.134-7-7-7-7 3.134-7 7 3.134 7 7 7zm48 25c3.866 0 7-3.134 7-7s-3.134-7-7-7-7 3.134-7 7 3.134 7 7 7zm-43-7c1.657 0 3-1.343 3-3s-1.343-3-3-3-3 1.343-3 3 1.343 3 3 3zm63 31c1.657 0 3-1.343 3-3s-1.343-3-3-3-3 1.343-3 3 1.343 3 3 3zM34 90c1.657 0 3-1.343 3-3s-1.343-3-3-3-3 1.343-3 3 1.343 3 3 3zm56-76c1.657 0 3-1.343 3-3s-1.343-3-3-3-3 1.343-3 3 1.343 3 3 3zM12 86c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm28-65c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm23-11c2.76 0 5-2.24 5-5s-2.24-5-5-5-5 2.24-5 5 2.24 5 5 5zm-6 60c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm29 22c2.76 0 5-2.24 5-5s-2.24-5-5-5-5 2.24-5 5 2.24 5 5 5zM32 63c2.76 0 5-2.24 5-5s-2.24-5-5-5-5 2.24-5 5 2.24 5 5 5zm57-13c2.76 0 5-2.24 5-5s-2.24-5-5-5-5 2.24-5 5 2.24 5 5 5zm-9-21c1.105 0 2-.895 2-2s-.895-2-2-2-2 .895-2 2 .895 2 2 2zM60 91c1.105 0 2-.895 2-2s-.895-2-2-2-2 .895-2 2 .895 2 2 2zM35 41c1.105 0 2-.895 2-2s-.895-2-2-2-2 .895-2 2 .895 2 2 2zM12 60c1.105 0 2-.895 2-2s-.895-2-2-2-2 .895-2 2 .895 2 2 2z' fill='%23ffffff' fill-opacity='0.1' fill-rule='evenodd'/%3E%3C/svg%3E')" }}></div>
          
          <div className="max-w-3xl text-center relative z-10">
            <span className="inline-block px-4 py-1 rounded-full bg-blue-800 bg-opacity-50 text-white text-sm font-medium mb-5">Austin's Premier Multifamily Listing Platform</span>
            <h1 className="text-4xl md:text-6xl font-extrabold tracking-tight mb-8 text-shadow-sm">
              Find Your Next <span className="text-cream-400">Multifamily</span> Investment
            </h1>
            <p className="text-xl md:text-2xl text-blue-100 font-light max-w-2xl mx-auto mb-10 leading-relaxed">
              Our interactive platform helps you discover, analyze, and track multifamily properties across Austin with comprehensive data and real-time updates.
            </p>
            <div className="flex flex-col sm:flex-row justify-center space-y-4 sm:space-y-0 sm:space-x-6">
              <Link href="/map" className="inline-flex items-center justify-center px-8 py-4 text-lg font-medium rounded-lg bg-cream-400 text-blue-900 hover:bg-cream-500 shadow-lg transform transition hover:-translate-y-1 hover:shadow-xl">
                <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l4.553 2.276A1 1 0 0021 18.382V7.618a1 1 0 00-.553-.894L15 4m0 13V4m0 0L9 7" />
                </svg>
                Explore Map
              </Link>
              <Link href="/signup" className="inline-flex items-center justify-center px-8 py-4 text-lg font-medium rounded-lg border-2 border-white text-white hover:bg-white hover:text-blue-700 transition-colors">
                <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                </svg>
                Sign Up Free
              </Link>
            </div>
          </div>
          
          {/* Stats bar */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-8 mt-16 bg-white bg-opacity-10 backdrop-blur-sm p-6 rounded-xl border border-white border-opacity-20 w-full max-w-5xl">
            <div className="text-center">
              <p className="text-3xl md:text-4xl font-bold text-cream-300">{properties.length || '150'}+</p>
              <p className="text-blue-100 mt-1">Properties</p>
            </div>
            <div className="text-center">
              <p className="text-3xl md:text-4xl font-bold text-cream-300">12K+</p>
              <p className="text-blue-100 mt-1">Total Units</p>
            </div>
            <div className="text-center">
              <p className="text-3xl md:text-4xl font-bold text-cream-300">$1.2B+</p>
              <p className="text-blue-100 mt-1">Property Value</p>
            </div>
            <div className="text-center">
              <p className="text-3xl md:text-4xl font-bold text-cream-300">24/7</p>
              <p className="text-blue-100 mt-1">Real-time Updates</p>
            </div>
          </div>
        </div>
      </section>

      {/* Featured Properties Section */}
      <section className="py-20 bg-cream-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-12">
            <span className="inline-block px-3 py-1 rounded-full bg-blue-100 text-blue-800 text-sm font-medium mb-3">Featured Listings</span>
            <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-4">Discover Austin Properties</h2>
            <p className="mt-2 text-xl text-gray-600 max-w-3xl mx-auto">
              Browse our latest multifamily properties added to the database
            </p>
          </div>

          {loading ? (
            <div className="flex justify-center items-center h-64">
              <div className="animate-pulse flex flex-col items-center">
                <div className="h-12 w-12 rounded-full bg-blue-200 mb-4"></div>
                <div className="h-4 w-36 bg-blue-200 rounded mb-2"></div>
                <div className="h-3 w-24 bg-gray-200 rounded"></div>
              </div>
            </div>
          ) : properties.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
              {properties.map((property: any) => (
                <div key={property.id} className="bg-cream-100 rounded-xl shadow-md overflow-hidden transition-all duration-300 hover:shadow-xl hover:-translate-y-1 group border border-cream-200">
                  <div className="h-48 bg-gradient-to-r from-blue-500 to-blue-600 relative overflow-hidden">
                    {/* Property image would go here */}
                    <div className="h-full flex items-center justify-center text-white">
                      <svg xmlns="http://www.w3.org/2000/svg" className="h-20 w-20 opacity-60 group-hover:scale-110 transition-transform duration-300" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
                      </svg>
                    </div>
                    {/* Status badge */}
                    <div className="absolute top-4 right-4">
                      <span className={`px-3 py-1 text-xs font-medium rounded-full ${
                        property.status === 'For Sale' 
                          ? 'bg-green-100 text-green-800' 
                          : 'bg-blue-100 text-blue-800'
                      }`}>
                        {property.status || 'Listed'}
                      </span>
                    </div>
                  </div>
                  <div className="p-6">
                    <h3 className="text-xl font-semibold text-gray-900 mb-2 group-hover:text-blue-600 transition-colors">
                      {property.name || `Property at ${property.address?.split(',')[0]}`}
                    </h3>
                    <p className="text-gray-600 mb-4 truncate">{property.address}</p>
                    <div className="grid grid-cols-2 gap-4 mb-4">
                      <div className="flex items-center text-sm text-gray-500">
                        <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 text-blue-500 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
                        </svg>
                        <span>Units: {property.num_units || property.units || 'N/A'}</span>
                      </div>
                      {property.year_built && (
                        <div className="flex items-center text-sm text-gray-500">
                          <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 text-blue-500 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                          </svg>
                          <span>Built: {property.year_built}</span>
                        </div>
                      )}
                    </div>
                    <Link href={`/map?propertyId=${property.id}`} className="text-blue-600 hover:text-blue-800 font-medium flex items-center mt-2 group-hover:underline">
                      View on Map
                      <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 ml-1 group-hover:translate-x-1 transition-transform" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                      </svg>
                    </Link>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-12 bg-cream-100 rounded-lg shadow border border-cream-200">
              <svg xmlns="http://www.w3.org/2000/svg" className="h-16 w-16 mx-auto text-blue-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
              </svg>
              <p className="mt-4 text-xl text-gray-500">No properties found.</p>
              <p className="mt-2 text-gray-500">
                Check back soon as we aggregate listings from across Austin.
              </p>
            </div>
          )}

          <div className="mt-12 text-center">
            <Link href="/map" className="inline-flex items-center px-6 py-3 border border-transparent text-base font-medium rounded-md shadow-md text-white bg-blue-600 hover:bg-blue-700 transition-all hover:shadow-lg">
              View All Properties
              <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 ml-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 8l4 4m0 0l-4 4m4-4H3" />
              </svg>
            </Link>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-20 bg-cream-100 relative overflow-hidden">
        {/* Background pattern */}
        <div className="absolute inset-0 opacity-5">
          <svg width="100%" height="100%" xmlns="http://www.w3.org/2000/svg">
            <defs>
              <pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse">
                <path d="M 0 10 L 40 10 M 10 0 L 10 40" stroke="#2563EB" strokeWidth="0.5" fill="none" />
              </pattern>
            </defs>
            <rect width="100%" height="100%" fill="url(#grid)" />
          </svg>
        </div>
        
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
          <div className="text-center mb-16">
            <span className="inline-block px-3 py-1 rounded-full bg-blue-100 text-blue-800 text-sm font-medium mb-3">Platform Benefits</span>
            <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-4">Why Use Our Platform</h2>
            <p className="mt-2 text-xl text-gray-600 max-w-3xl mx-auto">
              Our comprehensive tools help you make informed decisions about multifamily properties
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-10">
            <div className="bg-cream-50 p-8 rounded-xl shadow-md border border-cream-200 transform transition-all duration-300 hover:-translate-y-2 hover:shadow-lg">
              <div className="flex items-center justify-center h-16 w-16 rounded-full bg-blue-600 text-white mb-6 mx-auto">
                <svg xmlns="http://www.w3.org/2000/svg" className="h-8 w-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l4.553 2.276A1 1 0 0021 18.382V7.618a1 1 0 00-.553-.894L15 4m0 13V4m0 0L9 7" />
                </svg>
              </div>
              <h3 className="text-xl font-bold text-gray-900 mb-4 text-center">Interactive Map</h3>
              <p className="text-gray-600 text-center">
                Visualize property locations, filter by criteria, and get a geographical perspective of the Austin multifamily market.
              </p>
              <div className="mt-6 flex justify-center">
                <Link href="/map" className="text-blue-600 hover:text-blue-800 font-medium flex items-center">
                  Explore the Map
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 ml-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14 5l7 7m0 0l-7 7m7-7H3" />
                  </svg>
                </Link>
              </div>
            </div>
            
            <div className="bg-cream-50 p-8 rounded-xl shadow-md border border-cream-200 transform transition-all duration-300 hover:-translate-y-2 hover:shadow-lg">
              <div className="flex items-center justify-center h-16 w-16 rounded-full bg-blue-600 text-white mb-6 mx-auto">
                <svg xmlns="http://www.w3.org/2000/svg" className="h-8 w-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                </svg>
              </div>
              <h3 className="text-xl font-bold text-gray-900 mb-4 text-center">Comprehensive Data</h3>
              <p className="text-gray-600 text-center">
                Access detailed property information, market analytics, and investment metrics to support your decision-making process.
              </p>
              <div className="mt-6 flex justify-center">
                <Link href="/dashboard" className="text-blue-600 hover:text-blue-800 font-medium flex items-center">
                  View Dashboard
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 ml-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14 5l7 7m0 0l-7 7m7-7H3" />
                  </svg>
                </Link>
              </div>
            </div>
            
            <div className="bg-cream-50 p-8 rounded-xl shadow-md border border-cream-200 transform transition-all duration-300 hover:-translate-y-2 hover:shadow-lg">
              <div className="flex items-center justify-center h-16 w-16 rounded-full bg-blue-600 text-white mb-6 mx-auto">
                <svg xmlns="http://www.w3.org/2000/svg" className="h-8 w-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
                </svg>
              </div>
              <h3 className="text-xl font-bold text-gray-900 mb-4 text-center">Real-time Updates</h3>
              <p className="text-gray-600 text-center">
                Receive notifications about new listings, price changes, and market updates to stay ahead of opportunities.
              </p>
              <div className="mt-6 flex justify-center">
                <Link href="/signup" className="text-blue-600 hover:text-blue-800 font-medium flex items-center">
                  Get Alerts
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 ml-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14 5l7 7m0 0l-7 7m7-7H3" />
                  </svg>
                </Link>
              </div>
            </div>
          </div>
          
          {/* Testimonial */}
          <div className="mt-20 bg-cream-200 rounded-xl p-8 border border-cream-300">
            <div className="flex flex-col md:flex-row items-center md:items-start gap-8">
              <div className="w-24 h-24 rounded-full bg-blue-100 flex items-center justify-center flex-shrink-0">
                <svg xmlns="http://www.w3.org/2000/svg" className="h-12 w-12 text-blue-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                </svg>
              </div>
              <div>
                <svg className="h-8 w-8 text-blue-400 mb-4" fill="currentColor" viewBox="0 0 32 32">
                  <path d="M9.352 4C4.456 7.456 1 13.12 1 19.36c0 5.088 3.072 8.064 6.624 8.064 3.36 0 5.856-2.688 5.856-5.856 0-3.168-2.208-5.472-5.088-5.472-.576 0-1.344.096-1.536.192.48-3.264 3.552-7.104 6.624-9.024L9.352 4zm16.512 0c-4.8 3.456-8.256 9.12-8.256 15.36 0 5.088 3.072 8.064 6.624 8.064 3.264 0 5.856-2.688 5.856-5.856 0-3.168-2.304-5.472-5.184-5.472-.576 0-1.248.096-1.44.192.48-3.264 3.456-7.104 6.528-9.024L25.864 4z" />
                </svg>
                <p className="text-lg text-gray-700 italic mb-4">
                  This platform has transformed our property hunting process. The interactive map makes it easy to visualize options, and the real-time updates mean we never miss an opportunity.
                </p>
                <div>
                  <p className="font-semibold text-gray-900">Michael Roberts</p>
                  <p className="text-gray-600 text-sm">Investment Director, Austin Property Group</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="relative bg-blue-700 text-white py-16 lg:py-20 overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-tr from-blue-800 to-blue-600 opacity-90"></div>
        
        {/* Background pattern */}
        <div className="absolute inset-0 opacity-10">
          <svg xmlns="http://www.w3.org/2000/svg" width="100%" height="100%">
            <defs>
              <pattern id="dots" width="30" height="30" patternUnits="userSpaceOnUse">
                <circle cx="2" cy="2" r="2" fill="white" />
              </pattern>
            </defs>
            <rect width="100%" height="100%" fill="url(#dots)" />
          </svg>
        </div>
        
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center relative z-10">
          <h2 className="text-3xl md:text-4xl font-bold mb-6">Ready to Explore Austin Multifamily Properties?</h2>
          <p className="text-xl mb-10 max-w-3xl mx-auto text-blue-100">
            Sign up today to access our full platform features, save your searches, and receive property alerts.
          </p>
          
          <div className="max-w-lg mx-auto bg-white bg-opacity-10 backdrop-blur-sm p-8 rounded-xl border border-white border-opacity-20 mb-10">
            <form className="flex flex-col md:flex-row gap-4">
              <input 
                type="email"
                placeholder="Enter your email"
                className="flex-grow px-4 py-3 rounded-lg bg-white text-gray-900 focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
              <button 
                type="submit" 
                className="px-6 py-3 bg-cream-400 text-blue-900 font-medium rounded-lg hover:bg-cream-500 transition-colors"
              >
                Get Started
              </button>
            </form>
            <p className="text-sm mt-3 text-blue-200">We'll send you our property investor's guide for free</p>
          </div>
          
          <div className="flex flex-col sm:flex-row justify-center space-y-4 sm:space-y-0 sm:space-x-6">
            <Link href="/signup" className="inline-flex items-center justify-center px-8 py-4 border border-transparent text-lg font-medium rounded-lg shadow-lg bg-cream-400 text-blue-900 hover:bg-cream-500 transform transition hover:-translate-y-1">
              Create Free Account
            </Link>
            <Link href="/map" className="inline-flex items-center justify-center px-8 py-4 border-2 border-white text-lg font-medium rounded-lg text-white hover:bg-white hover:text-blue-700 transition-colors">
              Browse Map
            </Link>
          </div>
        </div>
      </section>
    </Layout>
  );
}