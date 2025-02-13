// message.schema.ts
import { Prop, Schema, SchemaFactory } from '@nestjs/mongoose';
import { Document } from 'mongoose';

export type MessageDocument = Message & Document;

@Schema()
export class Message {
  @Prop({ required: true })
  from_member_id: string;

  @Prop({ required: true })
  chat_id: string;

  @Prop({ required: true })
  message_id: string;

  @Prop({ required: true })
  message: string;

  @Prop({ required: true })
  message_type: string;

  @Prop({ required: true })
  timestamp: Date;
}

export const MessageSchema = SchemaFactory.createForClass(Message);
