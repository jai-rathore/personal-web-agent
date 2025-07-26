package server

import (
	"context"
	"fmt"
	"net/http"
	"strings"
	"time"

	"github.com/google/uuid"
	"github.com/jrathore/personal-web-agent/api/internal/config"
	"github.com/jrathore/personal-web-agent/api/internal/utils"
	"github.com/rs/cors"
	"github.com/rs/zerolog/log"
	"github.com/ulule/limiter/v3"
	"github.com/ulule/limiter/v3/drivers/middleware/stdlib"
	"github.com/ulule/limiter/v3/drivers/store/memory"
)

// RequestIDMiddleware adds a unique request ID to each request
func RequestIDMiddleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		requestID := r.Header.Get("X-Request-ID")
		if requestID == "" {
			requestID = uuid.New().String()
		}
		
		w.Header().Set("X-Request-ID", requestID)
		ctx := context.WithValue(r.Context(), utils.RequestIDKey, requestID)
		
		next.ServeHTTP(w, r.WithContext(ctx))
	})
}

// LoggingMiddleware logs HTTP requests and responses
func LoggingMiddleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		start := time.Now()
		ctx := context.WithValue(r.Context(), utils.StartTimeKey, start)
		
		// Create a response recorder to capture status
		recorder := &responseRecorder{ResponseWriter: w, statusCode: http.StatusOK}
		
		// Get request ID from context
		requestID := utils.GetRequestID(ctx)
		
		// Log request
		log.Info().
			Str("request_id", requestID).
			Str("method", r.Method).
			Str("path", r.URL.Path).
			Str("query", r.URL.RawQuery).
			Str("user_agent", r.UserAgent()).
			Str("remote_addr", getClientIP(r)).
			Msg("Request started")
		
		// Process request
		next.ServeHTTP(recorder, r.WithContext(ctx))
		
		// Log response
		duration := time.Since(start)
		log.Info().
			Str("request_id", requestID).
			Str("method", r.Method).
			Str("path", r.URL.Path).
			Int("status", recorder.statusCode).
			Dur("duration", duration).
			Msg("Request completed")
	})
}

// SecurityHeadersMiddleware adds security headers
func SecurityHeadersMiddleware(cfg *config.Config) func(http.Handler) http.Handler {
	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			// Content Security Policy
			csp := fmt.Sprintf(
				"default-src 'self'; "+
					"script-src 'self' 'unsafe-inline'; "+
					"style-src 'self' 'unsafe-inline'; "+
					"img-src 'self' data: https:; "+
					"connect-src 'self' %s; "+
					"frame-ancestors 'none'; "+
					"base-uri 'self'; "+
					"form-action 'self'",
				cfg.AllowedOrigin,
			)
			w.Header().Set("Content-Security-Policy", csp)
			
			// Other security headers
			w.Header().Set("X-Frame-Options", "DENY")
			w.Header().Set("X-Content-Type-Options", "nosniff")
			w.Header().Set("X-XSS-Protection", "1; mode=block")
			w.Header().Set("Referrer-Policy", "strict-origin-when-cross-origin")
			w.Header().Set("Permissions-Policy", "geolocation=(), microphone=(), camera=()")
			
			// HSTS for HTTPS
			if r.TLS != nil {
				w.Header().Set("Strict-Transport-Security", "max-age=31536000; includeSubDomains")
			}
			
			next.ServeHTTP(w, r)
		})
	}
}

// CORSMiddleware configures CORS
func CORSMiddleware(cfg *config.Config) *cors.Cors {
	return cors.New(cors.Options{
		AllowedOrigins: []string{cfg.AllowedOrigin},
		AllowedMethods: []string{
			http.MethodGet,
			http.MethodPost,
			http.MethodOptions,
		},
		AllowedHeaders: []string{
			"Accept",
			"Content-Type",
			"Content-Length",
			"Accept-Encoding",
			"X-CSRF-Token",
			"Authorization",
			"X-Request-ID",
			"Cache-Control",
		},
		ExposedHeaders: []string{
			"X-Request-ID",
		},
		AllowCredentials: false,
		MaxAge:           300, // 5 minutes
	})
}

// RateLimitMiddleware creates rate limiting middleware
func RateLimitMiddleware(rate limiter.Rate, burst int) func(http.Handler) http.Handler {
	store := memory.NewStore()
	rateLimiter := limiter.New(store, rate)
	middleware := stdlib.NewMiddleware(rateLimiter)
	
	return func(next http.Handler) http.Handler {
		return middleware.Handler(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			next.ServeHTTP(w, r)
		}))
	}
}

// TimeoutMiddleware adds request timeout
func TimeoutMiddleware(timeout time.Duration) func(http.Handler) http.Handler {
	return func(next http.Handler) http.Handler {
		return http.TimeoutHandler(next, timeout, "Request timeout")
	}
}

// RecoveryMiddleware recovers from panics
func RecoveryMiddleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		defer func() {
			if err := recover(); err != nil {
				requestID := utils.GetRequestID(r.Context())
				log.Error().
					Str("request_id", requestID).
					Interface("panic", err).
					Str("path", r.URL.Path).
					Msg("Panic recovered")
				
				http.Error(w, "Internal Server Error", http.StatusInternalServerError)
			}
		}()
		
		next.ServeHTTP(w, r)
	})
}


// responseRecorder wraps http.ResponseWriter to capture status code
type responseRecorder struct {
	http.ResponseWriter
	statusCode int
}

func (r *responseRecorder) WriteHeader(statusCode int) {
	r.statusCode = statusCode
	r.ResponseWriter.WriteHeader(statusCode)
}

// getClientIP extracts the real client IP address
func getClientIP(r *http.Request) string {
	// Check X-Forwarded-For header first (for load balancers/proxies)
	forwarded := r.Header.Get("X-Forwarded-For")
	if forwarded != "" {
		// Take the first IP in the list
		ips := strings.Split(forwarded, ",")
		if len(ips) > 0 {
			return strings.TrimSpace(ips[0])
		}
	}
	
	// Check X-Real-IP header
	realIP := r.Header.Get("X-Real-IP")
	if realIP != "" {
		return realIP
	}
	
	// Fall back to RemoteAddr
	ip := r.RemoteAddr
	if colonIndex := strings.LastIndex(ip, ":"); colonIndex != -1 {
		ip = ip[:colonIndex]
	}
	return ip
}