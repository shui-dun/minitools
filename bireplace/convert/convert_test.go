package convert

import (
	"bytes"
	"testing"
)

func TestToBytes(t *testing.T) {
	tests := []struct {
		name    string
		config  Config
		want    []byte
		wantErr bool
	}{
		{
			name: "valid string",
			config: Config{
				Value:  "hello",
				Type:   TypeString,
				Endian: EndianNone,
			},
			want:    []byte("hello"),
			wantErr: false,
		},
		{
			name: "string with invalid endian",
			config: Config{
				Value:  "hello",
				Type:   TypeString,
				Endian: EndianBig,
			},
			wantErr: true,
		},
		{
			name: "valid uint8",
			config: Config{
				Value:  "254",
				Type:   TypeDecimal,
				Endian: EndianBig,
				Length: 1,
			},
			want:    []byte{0xFE},
			wantErr: false,
		},
		{
			name: "uint8 overflow",
			config: Config{
				Value:  "256",
				Type:   TypeDecimal,
				Endian: EndianBig,
				Length: 1,
			},
			wantErr: true,
		},
		{
			name: "valid uint16 big endian",
			config: Config{
				Value:  "48225",
				Type:   TypeDecimal,
				Endian: EndianBig,
				Length: 2,
			},
			want:    []byte{0xBC, 0x61},
			wantErr: false,
		},
		{
			name: "valid uint16 little endian",
			config: Config{
				Value:  "48225",
				Type:   TypeDecimal,
				Endian: EndianLittle,
				Length: 2,
			},
			want:    []byte{0x61, 0xBC},
			wantErr: false,
		},
		{
			name: "uint16 overflow",
			config: Config{
				Value:  "65536",
				Type:   TypeDecimal,
				Endian: EndianBig,
				Length: 2,
			},
			wantErr: true,
		},
		{
			name: "valid uint32 big endian",
			config: Config{
				Value:  "305419896",
				Type:   TypeDecimal,
				Endian: EndianBig,
				Length: 4,
			},
			want:    []byte{0x12, 0x34, 0x56, 0x78},
			wantErr: false,
		},
		{
			name: "valid uint32 little endian",
			config: Config{
				Value:  "305419896",
				Type:   TypeDecimal,
				Endian: EndianLittle,
				Length: 4,
			},
			want:    []byte{0x78, 0x56, 0x34, 0x12},
			wantErr: false,
		},
		{
			name: "uint32 overflow",
			config: Config{
				Value:  "4294967296",
				Type:   TypeDecimal,
				Endian: EndianBig,
				Length: 4,
			},
			wantErr: true,
		},
		{
			name: "valid uint64 big endian",
			config: Config{
				Value:  "578437695752307201",
				Type:   TypeDecimal,
				Endian: EndianBig,
				Length: 8,
			},
			want:    []byte{0x08, 0x07, 0x06, 0x05, 0x04, 0x03, 0x02, 0x01},
			wantErr: false,
		},
		{
			name: "valid uint64 little endian",
			config: Config{
				Value:  "578437695752307201",
				Type:   TypeDecimal,
				Endian: EndianLittle,
				Length: 8,
			},
			want:    []byte{0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08},
			wantErr: false,
		},
		{
			name: "invalid decimal length 9",
			config: Config{
				Value:  "48225",
				Type:   TypeDecimal,
				Endian: EndianBig,
				Length: 9,
			},
			wantErr: true,
		},
		{
			name: "invalid decimal length 0",
			config: Config{
				Value:  "48225",
				Type:   TypeDecimal,
				Endian: EndianBig,
				Length: 0,
			},
			wantErr: true,
		},
		{
			name: "valid hex",
			config: Config{
				Value:  "FF00FF",
				Type:   TypeHex,
				Endian: EndianNone,
			},
			want:    []byte{0xFF, 0x00, 0xFF},
			wantErr: false,
		},
		{
			name: "hex with invalid endian",
			config: Config{
				Value:  "FF00FF",
				Type:   TypeHex,
				Endian: EndianBig,
			},
			wantErr: true,
		},
		{
			name: "invalid hex value",
			config: Config{
				Value: "not hex",
				Type:  TypeHex,
			},
			wantErr: true,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			got, err := ToBytes(tt.config)
			if (err != nil) != tt.wantErr {
				t.Errorf("ToBytes() error = %v, wantErr %v", err, tt.wantErr)
				return
			}
			if !tt.wantErr && !bytes.Equal(got, tt.want) {
				t.Errorf("ToBytes() = %v, want %v", got, tt.want)
			}
		})
	}
}
