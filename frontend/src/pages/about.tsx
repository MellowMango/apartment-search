import React from 'react';
import Layout from '../components/Layout';

const About: React.FC = () => {
  return (
    <Layout title="About | Austin Multifamily Map">
      <div className="container mx-auto px-4 py-12">
        <div className="max-w-4xl mx-auto">
          <h1 className="text-4xl font-bold text-gray-800 mb-6">About Austin Multifamily Map</h1>
          
          <div className="bg-white shadow-md rounded-lg p-8 mb-8">
            <h2 className="text-2xl font-semibold text-gray-700 mb-4">Our Mission</h2>
            <p className="text-gray-600 mb-6">
              Austin Multifamily Map aims to provide comprehensive, up-to-date information about multifamily 
              properties in the Austin area. We aggregate data from multiple sources to give investors, 
              property managers, and researchers the most accurate information about the Austin real estate market.
            </p>
            
            <h2 className="text-2xl font-semibold text-gray-700 mb-4">What We Offer</h2>
            <ul className="list-disc pl-6 text-gray-600 mb-6 space-y-2">
              <li>Interactive map of multifamily properties in Austin</li>
              <li>Detailed property information including units, price, and amenities</li>
              <li>Market analytics and investment metrics</li>
              <li>Risk assessment tools for potential investments</li>
              <li>Real-time updates on new listings and property changes</li>
            </ul>
            
            <h2 className="text-2xl font-semibold text-gray-700 mb-4">Our Data</h2>
            <p className="text-gray-600 mb-6">
              We collect data from multiple sources including public records, broker listings, 
              and proprietary databases. Our team cleans and enriches this data to provide the most 
              accurate and comprehensive information available. We update our database regularly 
              to ensure the information is current and relevant.
            </p>
          </div>
          
          <div className="bg-white shadow-md rounded-lg p-8">
            <h2 className="text-2xl font-semibold text-gray-700 mb-4">Our Team</h2>
            <p className="text-gray-600 mb-6">
              Our team consists of real estate professionals, data scientists, and software engineers 
              who are passionate about making real estate data more accessible and useful. 
              We combine industry expertise with cutting-edge technology to create a platform 
              that serves the needs of the Austin real estate community.
            </p>
            
            <h2 className="text-2xl font-semibold text-gray-700 mb-4">Contact Us</h2>
            <p className="text-gray-600">
              Have questions or feedback? We'd love to hear from you. 
              Please contact us at <a href="mailto:info@austinmultifamilymap.com" className="text-blue-600 hover:underline">info@austinmultifamilymap.com</a>.
            </p>
          </div>
        </div>
      </div>
    </Layout>
  );
};

export default About;