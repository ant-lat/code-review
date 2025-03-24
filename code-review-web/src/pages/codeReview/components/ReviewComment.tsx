import React, { useState, useEffect } from 'react';
import { List, Avatar, Form, Button, Input, Tooltip, message } from 'antd';
import { UserOutlined, DeleteOutlined } from '@ant-design/icons';
import moment from 'moment';
import { useSelector } from 'react-redux';
import { getReviewComments, addReviewComment, deleteReviewComment } from '../../../api/codeReview';
import { CodeReviewComment } from '../../../api/types';

const { TextArea } = Input;

interface ReviewCommentProps {
  reviewId: number;
}

const CommentItem = ({ comment, currentUser, onDelete }: {
  comment: CodeReviewComment;
  currentUser: any;
  onDelete: (id: number) => void;
}) => (
  <div className="comment-item" style={{ marginBottom: 16, borderBottom: '1px solid #f0f0f0', paddingBottom: 8 }}>
    <div style={{ display: 'flex', alignItems: 'flex-start' }}>
      <Avatar icon={<UserOutlined />} />
      <div style={{ marginLeft: 8, flex: 1 }}>
        <div>
          <span style={{ fontWeight: 'bold' }}>{comment.user?.username}</span>
          <Tooltip title={moment(comment.created_at).format('YYYY-MM-DD HH:mm:ss')}>
            <span style={{ marginLeft: 8, color: '#999' }}>{moment(comment.created_at).fromNow()}</span>
          </Tooltip>
        </div>
        <div style={{ margin: '8px 0' }}>{comment.content}</div>
        {currentUser && currentUser.id === comment.user_id && (
          <Button 
            type="text" 
            danger 
            icon={<DeleteOutlined />} 
            onClick={() => onDelete(comment.id)}
            size="small"
          >
            删除
          </Button>
        )}
      </div>
    </div>
  </div>
);

const ReviewComment: React.FC<ReviewCommentProps> = ({ reviewId }) => {
  const [comments, setComments] = useState<CodeReviewComment[]>([]);
  const [submitting, setSubmitting] = useState(false);
  const [value, setValue] = useState('');
  const [loading, setLoading] = useState(false);
  const [form] = Form.useForm();
  const currentUser = useSelector((state: any) => state.auth.user);

  const fetchComments = async () => {
    try {
      setLoading(true);
      const response = await getReviewComments(reviewId);
      setComments(response.data || []);
    } catch (error) {
      message.error('获取评论失败');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (reviewId) {
      fetchComments();
    }
  }, [reviewId]);

  const handleSubmit = async () => {
    if (!value.trim()) {
      message.warning('评论内容不能为空');
      return;
    }

    try {
      setSubmitting(true);
      await addReviewComment(reviewId, {
        review_id: reviewId,
        content: value,
        file_path: '' // 使用空字符串表示通用评论，而非特定文件行的评论
      });
      setValue('');
      fetchComments();
      message.success('添加评论成功');
    } catch (error) {
      message.error('添加评论失败');
    } finally {
      setSubmitting(false);
    }
  };

  const handleDelete = async (commentId: number) => {
    try {
      await deleteReviewComment(reviewId, commentId);
      message.success('删除评论成功');
      fetchComments();
    } catch (error) {
      message.error('删除评论失败');
    }
  };

  return (
    <div className="review-comments">
      <List
        loading={loading}
        dataSource={comments}
        header={`${comments.length} 条评论`}
        renderItem={item => (
          <CommentItem comment={item} currentUser={currentUser} onDelete={handleDelete} />
        )}
      />
      
      {currentUser && (
        <div className="comment-editor" style={{ marginTop: 16 }}>
          <Form form={form} onFinish={handleSubmit}>
            <Form.Item>
              <TextArea 
                rows={4} 
                value={value} 
                onChange={e => setValue(e.target.value)} 
                placeholder="添加评论..."
              />
            </Form.Item>
            <Form.Item>
              <Button 
                htmlType="submit" 
                loading={submitting} 
                type="primary"
                disabled={!value.trim()}
              >
                提交评论
              </Button>
            </Form.Item>
          </Form>
        </div>
      )}
    </div>
  );
};

export default ReviewComment; 