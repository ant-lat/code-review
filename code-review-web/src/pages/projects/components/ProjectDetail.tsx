import React, { useState, useEffect } from 'react';
import { Tabs, Card } from 'antd';
import MemberList from './MemberList';
import { getProjectMembers } from '../../../api/projects';

const { TabPane } = Tabs;

interface ProjectDetailProps {
  projectId: number;
}

const ProjectDetail: React.FC<ProjectDetailProps> = ({ projectId }) => {
  const [members, setMembers] = useState([]);
  const [loading, setLoading] = useState(false);

  const fetchMembers = async () => {
    setLoading(true);
    try {
      const res = await getProjectMembers(projectId);
      if (res.code === 200 && res.data) {
        setMembers(res.data);
      }
    } catch (error) {
      console.error('获取项目成员失败:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchMembers();
  }, [projectId]);

  return (
    <Card>
      <Tabs defaultActiveKey="members">
        <TabPane tab="成员管理" key="members">
          <MemberList
            projectId={projectId}
            members={members}
            onMemberUpdate={fetchMembers}
          />
        </TabPane>
        {/* 可以添加更多标签页，如项目设置、统计信息等 */}
      </Tabs>
    </Card>
  );
};

export default ProjectDetail; 