# ========================================
# Build Stage
# ========================================
FROM golang:1.24-alpine AS builder

# Set the Current Working Directory inside the container
WORKDIR /app

# Copy go mod and sum files
COPY go.mod go.sum ./

# Download all dependencies.
RUN go mod download

# Copy the source code into the container
COPY . .

# Build the Go app. Disable CGO since we are using pure Go SQLite.
RUN CGO_ENABLED=0 GOOS=linux go build -a -installsuffix cgo -o api-server .

# ========================================
# Production Stage
# ========================================
FROM alpine:latest

WORKDIR /app

# Add bash and ca-certificates
RUN apk --no-cache add ca-certificates bash tzdata

# Copy the Pre-built binary file from the previous stage
COPY --from=builder /app/api-server .

# Expose port 3000 to the outside world
EXPOSE 3000

# Command to run the executable
CMD ["./api-server"]
