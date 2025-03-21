FROM node:20.19.0-alpine AS development

WORKDIR /app

COPY package.json package-lock.json ./

RUN npm install

COPY . .

RUN npm run build

FROM nginx:latest AS production

EXPOSE 3000

COPY --from=development /app/dist /usr/share/nginx/html

COPY nginx.conf /etc/nginx/conf.d/default.conf
