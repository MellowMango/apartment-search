import React from 'react';
import { Box, Container } from '@chakra-ui/react';
import { withPageAuthRequired } from '@auth0/nextjs-auth0';
import AdminLayout from '../../components/layouts/AdminLayout';
import PropertyCorrectionsReview from '../../components/admin/PropertyCorrectionsReview';
import { checkUserIsAdmin } from '../../utils/auth';

export const getServerSideProps = withPageAuthRequired({
  async getServerSideProps(context) {
    // Check if user is admin
    const isAdmin = await checkUserIsAdmin(context.req, context.res);
    
    if (!isAdmin) {
      return {
        redirect: {
          destination: '/unauthorized',
          permanent: false,
        },
      };
    }
    
    return {
      props: {},
    };
  },
});

const CorrectionsPage = () => {
  return (
    <AdminLayout title="Property Corrections">
      <Container maxW="container.xl" py={6}>
        <PropertyCorrectionsReview />
      </Container>
    </AdminLayout>
  );
};

export default CorrectionsPage; 