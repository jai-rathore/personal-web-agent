package content

import (
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"strings"
	"sync"

	"github.com/jrathore/personal-web-agent/api/internal/types"
	"github.com/rs/zerolog/log"
)

// Loader manages content packs
type Loader struct {
	contentDir string
	packs      map[string]*types.Pack
	checksums  map[string]string
	mu         sync.RWMutex
}

// NewLoader creates a new content loader
func NewLoader(contentDir string) *Loader {
	return &Loader{
		contentDir: contentDir,
		packs:      make(map[string]*types.Pack),
		checksums:  make(map[string]string),
	}
}

// Load loads all content packs from the manifest
func (l *Loader) Load() error {
	l.mu.Lock()
	defer l.mu.Unlock()
	
	// Read manifest
	manifestPath := filepath.Join(l.contentDir, "packs.json")
	manifestData, err := os.ReadFile(manifestPath)
	if err != nil {
		return fmt.Errorf("failed to read manifest: %w", err)
	}
	
	var manifest types.PackManifest
	if err := json.Unmarshal(manifestData, &manifest); err != nil {
		return fmt.Errorf("failed to parse manifest: %w", err)
	}
	
	// Clear existing packs
	l.packs = make(map[string]*types.Pack)
	l.checksums = make(map[string]string)
	
	// Load each pack
	for _, pack := range manifest.Packs {
		// Convert relative path to absolute path
		packPath := pack.Path
		if !filepath.IsAbs(packPath) {
			// If path starts with "content/", remove it since we're already in content dir
			if strings.HasPrefix(packPath, "content/") {
				packPath = strings.TrimPrefix(packPath, "content/")
			}
			packPath = filepath.Join(l.contentDir, packPath)
		}
		
		// Read content
		content, err := os.ReadFile(packPath)
		if err != nil {
			log.Error().Err(err).Str("pack", pack.ID).Str("path", packPath).Msg("Failed to load pack")
			continue
		}
		
		// Calculate checksum
		hash := sha256.Sum256(content)
		checksum := hex.EncodeToString(hash[:])
		
		// Store pack
		packCopy := pack
		packCopy.Content = string(content)
		packCopy.Checksum = checksum
		l.packs[pack.ID] = &packCopy
		l.checksums[pack.ID] = checksum
		
		log.Info().
			Str("pack", pack.ID).
			Str("path", packPath).
			Int("size", len(content)).
			Str("checksum", checksum[:8]).
			Msg("Loaded content pack")
	}
	
	log.Info().Int("count", len(l.packs)).Msg("Content packs loaded")
	return nil
}

// GetPack returns a pack by ID
func (l *Loader) GetPack(id string) (*types.Pack, bool) {
	l.mu.RLock()
	defer l.mu.RUnlock()
	
	pack, ok := l.packs[id]
	return pack, ok
}

// GetPacksByHints returns packs that match the given hints
func (l *Loader) GetPacksByHints(hints []string) []*types.Pack {
	l.mu.RLock()
	defer l.mu.RUnlock()
	
	var matches []*types.Pack
	
	// Convert hints to lowercase for case-insensitive matching
	lowerHints := make([]string, len(hints))
	for i, hint := range hints {
		lowerHints[i] = strings.ToLower(hint)
	}
	
	for _, pack := range l.packs {
		for _, packHint := range pack.TopicHints {
			packHintLower := strings.ToLower(packHint)
			for _, hint := range lowerHints {
				if strings.Contains(packHintLower, hint) || strings.Contains(hint, packHintLower) {
					matches = append(matches, pack)
					goto nextPack
				}
			}
		}
	nextPack:
	}
	
	return matches
}

// GetAllPacks returns all loaded packs
func (l *Loader) GetAllPacks() []*types.Pack {
	l.mu.RLock()
	defer l.mu.RUnlock()
	
	packs := make([]*types.Pack, 0, len(l.packs))
	for _, pack := range l.packs {
		packs = append(packs, pack)
	}
	return packs
}

// GetChecksums returns all pack checksums
func (l *Loader) GetChecksums() map[string]string {
	l.mu.RLock()
	defer l.mu.RUnlock()
	
	checksums := make(map[string]string)
	for k, v := range l.checksums {
		checksums[k] = v
	}
	return checksums
}