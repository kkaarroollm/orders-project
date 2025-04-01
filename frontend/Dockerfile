FROM node:20.19.0-alpine AS development

WORKDIR /app

COPY package*.json ./

RUN npm install

COPY . .

ARG VITE_ENV=production
RUN npm run build -- --mode $VITE_ENV

FROM nginx:latest AS production

COPY --from=development /app/dist /usr/share/nginx/html

COPY nginx.conf /etc/nginx/conf.d/default.conf
