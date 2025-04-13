import React from 'react';
import { Box, Container } from '@chakra-ui/react';
// import { withPageAuthRequired } from '@auth0/nextjs-auth0'; // Commented out
// import AdminLayout from '../../components/layouts/AdminLayout'; // Commented out - file doesn't exist
// import PropertyCorrectionsReview from '../../components/admin/PropertyCorrectionsReview'; // Commented out - file doesn't exist
// import { checkUserIsAdmin } from '../../utils/auth'; // Commented out - file doesn't exist

/* // Commented out getServerSideProps
export const getServerSideProps = withPageAuthRequired({
  async getServerSideProps(context: any) { // Added type for context
    // Check if user is admin
    // const isAdmin = await checkUserIsAdmin(context.req, context.res);
    
    // if (!isAdmin) {
    //   return {
    //     redirect: {
    //       destination: '/unauthorized',
    //       permanent: false,
    //     },
    //   };
    // }
    
    return {
      props: {},
    };
  },
});
*/

const CorrectionsPage = () => {
  return (
    // <AdminLayout title="Property Corrections"> // Commented out usage
      <Container maxW="container.xl" py={6}>
        {/* <PropertyCorrectionsReview /> */ /* Commented out usage */}
        <div>Property Corrections Content Placeholder</div> {/* Added placeholder content */}
      </Container>
    // </AdminLayout> // Commented out usage
  );
};

export default CorrectionsPage; 