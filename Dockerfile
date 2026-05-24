FROM nginx:1.27-alpine

COPY . /usr/share/nginx/html
RUN rm -f /usr/share/nginx/html/Dockerfile \
          /usr/share/nginx/html/.dockerignore \
          /usr/share/nginx/html/deploy.sh \
          /usr/share/nginx/html/run.sh \
          /usr/share/nginx/html/CLAUDE.md

EXPOSE 80
