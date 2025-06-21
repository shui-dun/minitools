package convert

import (
	"encoding/binary"
	"encoding/hex"
	"fmt"
	"strconv"
)

type ValueType int

const (
	TypeString ValueType = iota
	TypeDecimal
	TypeHex
)

type Endianness int

const (
	EndianBig Endianness = iota
	EndianLittle
	EndianNone
)

// ParseValueType 将字符串转换为 ValueType
func ParseValueType(s string) (ValueType, error) {
	switch s {
	case "string":
		return TypeString, nil
	case "dec":
		return TypeDecimal, nil
	case "hex":
		return TypeHex, nil
	default:
		return TypeString, fmt.Errorf("unknown type: %s", s)
	}
}

// ParseEndianness 将字符串转换为 Endianness
func ParseEndianness(s string) (Endianness, error) {
	switch s {
	case "":
		return EndianNone, nil
	case "big":
		return EndianBig, nil
	case "little":
		return EndianLittle, nil
	default:
		return EndianNone, fmt.Errorf("unknown endianness: %s", s)
	}
}

type Config struct {
	Value  string
	Type   ValueType
	Endian Endianness
	Length int
}

// ToBytes 根据配置将数据转换为字节切片
func ToBytes(cfg Config) ([]byte, error) {
	switch cfg.Type {
	case TypeString:
		if cfg.Endian != EndianNone || cfg.Length != 0 {
			return nil, fmt.Errorf("endian and length parameters are not allowed for string type")
		}
		return []byte(cfg.Value), nil

	case TypeDecimal:
		if cfg.Endian == EndianNone || cfg.Length == 0 {
			return nil, fmt.Errorf("endian and length parameters are required for decimal type")
		}
		if cfg.Length < 1 || cfg.Length > 8 {
			return nil, fmt.Errorf("length must be between 1 and 8 bytes for decimal type")
		}

		num, err := strconv.ParseUint(cfg.Value, 10, 64)
		if err != nil {
			return nil, fmt.Errorf("parsing decimal value: %w", err)
		}

		// 检查数字是否适合指定的长度
		maxValue := uint64(1)<<uint(cfg.Length*8) - 1
		if num > maxValue {
			return nil, fmt.Errorf("value %d is too large for %d bytes", num, cfg.Length)
		}

		bytes := make([]byte, cfg.Length)
		switch cfg.Length {
		case 1:
			bytes[0] = byte(num)
		default:
			buf := make([]byte, 8)
			if cfg.Endian == EndianBig {
				binary.BigEndian.PutUint64(buf, num)
				copy(bytes, buf[8-cfg.Length:])
			} else {
				binary.LittleEndian.PutUint64(buf, num)
				copy(bytes, buf[:cfg.Length])
			}
		}
		return bytes, nil

	case TypeHex:
		if cfg.Endian != EndianNone || cfg.Length != 0 {
			return nil, fmt.Errorf("endian and length parameters are not allowed for hex type")
		}
		bytes, err := hex.DecodeString(cfg.Value)
		if err != nil {
			return nil, fmt.Errorf("parsing hex value: %w", err)
		}
		return bytes, nil

	default:
		return nil, fmt.Errorf("unknown type: %v", cfg.Type)
	}
}
