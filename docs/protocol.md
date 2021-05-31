DEFAULT PORT OF COMMUNICATION IS 48999


# **Packet Format**


All packets starts with ID of the packet

Followed by length of the packet

All packets ends with 1 byte CRC-8 Parity Byte

| PACKET ID (1 byte) | Packet Length (2 bytes) | PAYLOAD (var length) | CRC-8 (1 byte) |
|:-------------------|:------------------------|:---------------------|:---------------|




Field types

| Type Name          | Type Length (bytes) | Values / Description  | Notes                                                                                |
|:-------------------|:--------------------|:----------------------|:-------------------------------------------------------------------------------------|
| byte               | 1                   | uint8_t               |                                                                                      |
| short              | 2                   | uint16_t              |                                                                                      |
| unsigned long      | 4                   | uint32_t              |                                                                                      |
| unsigned long long | 8                   | uint64_t              |                                                                                      |
| string             | 2 + varlong         | string                | First 2 bytes are length of a string (X) . Then NULL-Terminated string of a length X |
| capabilities_flag  | 1                   | Flags of capabilities |                                                                                      |
| pixel              | 7                   | Pixel with RGB Color  | 2x2 bytes - X, Y coordinates, followed by 3 byte RGB value                           |
| SensorType         | 1                   | Sensor type           |                                                                                      |
| FileResponseType   | 1                   | File Response type    |                                                                                      |

FileOperationType

| ID | VALUE   |
|:---|:--------|
| 0  | UNKNOWN |
| 1  | LS      |
| 2  | MKDIR   |
| 3  | TOUCH   |
| 4  | DEL     |
| 5  | MV      |
| 6  | CP      |
| 7  | DOWN    |
|    |         |




FileResponseType

| ID | Value     |
|:---|:----------|
| 0  | UNKNOWN   |
| 1  | OK        |
| 2  | NOT_FOUND |
| 3  | INVALID   |
| 4  |           |

SensorType:

| ID | Value                |
|:---|:---------------------|
| 0  | UNKNOWN              |
| 1  | TEMPERATURE_HUMIDITY |
| 2  | TEMPERATURE          |
| 3  | HUMIDITY             |
| 4  | CURRENT_VOLTAGE      |
| 5  | IR_RECEIVER          |
| 6  | CONTACTRON           |
| 7  | MAGNETIC_SENSOR      |
| 8  | ADC                  |
| 9  | DIGITAL_PIN          |


AnimationMode

| ID | Value               |
|:---|:--------------------|
| 0  | UNKNOWN             |
| 1  | TEST_MODE           |
| 2  | ANIMATION_FROM_FILE |
| 3  | LIVE_ANIMATION      |
| 3  |                     |

Pixel:

| Field Name | FieldType | Note         |
|:-----------|:----------|:-------------|
| X          | byte      | x-coordinate |
| Y          | byte      | y-coordinate |
| R          | byte      | red          |
| G          | byte      | green        |
| B          | byte      | blue         |



Capabilities Json:

Root:

"global_settings" - object containing global settings of Visor
- "maxFPS": 30 - Max FPS speed of the screen
- "maxEventResolutionSecond": 0.5 - Min refresh time of all events
- "maxPacketSize": 64000 - max packet size in bytes


BLA BLA BLA





####  Clientbound packets (Visor -> App)

| ID   | Name         | Shortcut | Note                                                         |
|:-----|:-------------|:---------|:-------------------------------------------------------------|
| 0x01 | \[RESERVED\] | ACK      | RESERVED                                                     |
| 0x02 | \[RESERVED\] | ERR      | RESERVED                                                     |
| 0x03 | Handshake    | HND      | Handshake to establish communication and exchange start data |
| 0x04 | LogSensor    | LSR      | Log data from sensor                                         |
| 0x05 | FileResponse | FIR      | Response on file event                                       |
| 0x06 | FileDownload | FDW      | Download the file to the client                               |


#### Serverbound packers (App -> Visor)
| ID   | Name                 | Shortcut | Note                                                         |
|:-----|:---------------------|:---------|:-------------------------------------------------------------|
| 0x01 | \[RESERVED\]         | ACK      | RESERVED                                                     |
| 0x02 | \[RESERVED\]         | ERR      | RESERVED                                                     |
| 0x03 | Handshake            | HND      | Handshake to establish communication and exchange start data |
| 0x04 | ChangeAnimation      | CAN      | Changes animation on display                                 |
| 0x05 | RequestSensor        | RQS      | Requests data from sensor                                    |
| 0x06 | TimeUpdate           | TUP      | Update current time in system                                |
| 0x07 | ChangeSystemProperty | CSP      | Changes given system property                                |
| 0x08 | ChangeDrawingMode    | CDM      | Changes current animation drawing mode                       |
| 0x09 | DrawUpdate           | DWU      | Draw update when in realtime mode                            |
| 0x0A | RequestShutdown      | RQD      | Request shutdown on the device                               |
| 0x0B | RegisterEvent        | REV      | Register event for updating the value                        |
| 0x0C | FileOperation        | FOP      | File Operation                                               |
| 0x0D | FileUpload           | FUP      | File upload operation                                        |
| 0x0E | ControlSet           | CTS      | Sets value to controller                                     |



# **Packet descriptions**

##  **Clientbound**
- 0x01 RESERVED

| Field Name             | FieldType | Note |
|:-----------------------|:----------|:-----|
| |           |      |

- 0x02 RESERVED

| Field Name | FieldType | Note |
|:-----------|:----------|:-----|
|            |           |      |

- 0x03 Handshake - Packet used to send data about current system configuration and abilities

| Field Name | FieldType | Note                              |
|:-----------|:----------|:----------------------------------|
| json       | string   | Json with the CAPABILITIES object |

- 0x04 LogSensor - Log data from sensor

| Field Name  | FieldType  | Note                                                                       |
|:------------|:-----------|:---------------------------------------------------------------------------|
| sensor_id   | byte       | Sensor ID                                                                  |
| log_source  | byte       | 0 if request was manual, >0 if triggered by registered event timer handler |
| sensor_type | SensorType | Sensor Type                                                                |
| value       | string     | Value data                                                                 |

- 0x05  FileResponse - Response on file event

| Field Name    | FieldType        | Note                |
|:--------------|:-----------------|:--------------------|
| request_id    | byte             | Response request ID |
| response_type | FileResponseType | File response type  |
| response      | string           | Response data       |

- 0x06 File Download - Download file from the device

**WARNING!** There is no multi-part system in this moment. One file can NOT be longer then MAX_PACKET size!


| Field Name | FieldType | Note                      |
|:-----------|:----------|:--------------------------|
| request_id | byte      | Response request ID       |
| file_name  | string    | Filename to Download      |
| size       | short     | Filesize in bytes         |
| binary     | bytes     | Binary stream of the file |

## ServerBound

**JSONS DATA**

- 0x01 RESERVED

| Field Name             | FieldType | Note |
|:-----------------------|:----------|:-----|
| |           |      |

- 0x02 RESERVED

| Field Name | FieldType | Note |
|:-----------|:----------|:-----|
|            |           |      |
- 0x03 Handshake - Packet used to indicate successful app connection and asks for data

| Field Name  | FieldType | Note        |
|:------------|:----------|:------------|
| app_version | uint8_t   | app version |

- 0x04 ChangeAnimation - Changes animation on display

| Field Name     | FieldType | Note                          |
|:---------------|:----------|:------------------------------|
| animation_name | string    | name of the animation to play |

- 0x05 RequestSensor - Requests data from sensor

| Field Name | FieldType | Note      |
|:-----------|:----------|:----------|
| sensor_id  | byte      | Sensor id |

- 0x06 TimeUpdate - Update current time in system

| Field Name   | FieldType          | Note                    |
|:-------------|:-------------------|:------------------------|
| current_time | unsigned long long | current time from epoch |


- 0x07 ChangeSystemProperty - Changes given system property

| Field Name     | FieldType | Note               |
|:---------------|:----------|:-------------------|
| property_name  | string    | property to change |
| property_value | string    | property value     |

- 0x07 ChangeSystemProperty - Changes given system property

| Field Name     | FieldType | Note               |
|:---------------|:----------|:-------------------|
| property_name  | string    | property to change |
| property_value | string    | property value     |


- 0x08 ChangeDrawingMode - Changes current animation drawing mode

| Field Name     | FieldType     | Note                  |
|:---------------|:--------------|:----------------------|
| animation_mode | AnimationMode | target animation mode |



- 0x09 DrawUpdate - Packet used to draw on the destination

| Field Name | FieldType  | Note                             |
|:-----------|:-----------|:---------------------------------|
| screen_id  | byte       | screen id to draw on             |
| command    | byte       | 0 - draw pixel, 1 - clear screen |
| length     | byte       | number of pixels to update       |
| pixel[]    | pixel list | list of pixels to update         |

- 0x0A RequestShutdown  - Request shutdown on the device

| Field Name | FieldType | Note |
|:-----------|:----------|:-----|
|            |           |      |


- 0x0C FileOperation - File Operation

| Field Name   | FieldType         | Note                        |
|:-------------|:------------------|:----------------------------|
| request_id   | byte              | ID of the request           |
| operation_id | FileOperationType | ID of the operation to make |
| working_dir  | string            | Working dir                 |
| parameters   | string            | Parameters of the data      |

 - 0x0D FileUpload - Upload file to the device

**WARNING!** There is no multi-part system in this moment. One file can NOT be longer then MAX_PACKET size!

| Field Name  | FieldType | Note                      |
|:------------|:----------|:--------------------------|
| request_id  | byte      | Request ID                |
| file_name   | string    | Filename to upload        |
| working_dir | string    | Folder to upload to       |
| size        | short     | Filesize in bytes         |
| binary      | bytes     | Binary stream of the file |

- 0x0E ControlSet - Sets value to controller

| Field Name    | FieldType | Note               |
|:--------------|:----------|:-------------------|
| control_id    | byte      | ID Of control      |
| control_value | string    | value of controler |
