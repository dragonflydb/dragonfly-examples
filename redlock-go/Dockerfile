FROM golang:1.20 as builder

WORKDIR /app

COPY go.mod go.sum ./
RUN go mod download

COPY app/ ./app/

RUN CGO_ENABLED=0 GOOS=linux go build -v -o /go/bin/app ./app/main.go

FROM alpine:latest

COPY --from=builder /go/bin/app /go/bin/app

CMD ["/go/bin/app"]
