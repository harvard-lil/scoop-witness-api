# Python dependencies
poetry install;

# Node dependencies
npm install;

# Pull RDS certs
curl https://truststore.pki.rds.amazonaws.com/global/global-bundle.pem > rds.pem;