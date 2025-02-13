export interface MessageDto {
  message: string;
  message_type: string;
  message_id: string;
  from_member_id: string;
  from_member_name: string;
  chat_id: string;
  timestamp: Date;
}
